from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.workflow.models import ServiceVisitItem, ServiceVisit
from .models import ServiceReportProfile, ReportInstance, ReportValue, ReportProfile, ReportParameter
from .serializers import (
    ReportProfileSerializer, ReportInstanceSerializer, ReportValueSerializer, ReportSaveSerializer
)

class ReportWorkItemViewSet(viewsets.ViewSet):
    """
    Endpoints for reporting on a specific ServiceVisitItem.
    Lookup field is 'pk' mapping to ServiceVisitItem.id
    """
    permission_classes = [IsAuthenticated]

    def _get_item(self, pk):
        return get_object_or_404(ServiceVisitItem, pk=pk)

    def _get_profile(self, item):
        # Find profile for the service
        # Logic: Check ServiceReportProfile first
        srp = ServiceReportProfile.objects.filter(service=item.service).first()
        if not srp:
            raise exceptions.NotFound("No report profile associated with this service.")
        return srp.profile

    def _get_instance(self, item):
        try:
            return item.report_instance
        except ReportInstance.DoesNotExist:
            return None

    @action(detail=True, methods=["get"])
    def schema(self, request, pk=None):
        item = self._get_item(pk)
        profile = self._get_profile(item)
        serializer = ReportProfileSerializer(profile)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def values(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
            return Response({
                "status": "draft",
                "values": []
            })
        
        serializer = ReportValueSerializer(instance.values.all(), many=True)
        return Response({
            "status": instance.status,
            "values": serializer.data
        })

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        item = self._get_item(pk)
        profile = self._get_profile(item)
        
        # Check if already submitted/verified (locked)
        instance = self._get_instance(item)
        if instance and instance.status in ["submitted", "verified"]:
            raise exceptions.PermissionDenied("Cannot edit a submitted report.")

        save_serializer = ReportSaveSerializer(data=request.data)
        save_serializer.is_valid(raise_exception=True)
        values_list = save_serializer.validated_data["values"]

        with transaction.atomic():
            if not instance:
                instance = ReportInstance.objects.create(
                    service_visit_item=item,
                    profile=profile,
                    created_by=request.user,
                    status="draft"
                )
            
            # Simple bulk update/create logic
            current_values = {str(v.parameter_id): v for v in instance.values.all()}
            
            for item_data in values_list:
                param_id = str(item_data["parameter_id"])
                val = item_data["value"]
                
                # val might be list or string, save as string/JSON
                if isinstance(val, (list, dict)):
                    import json
                    val_str = json.dumps(val)
                else:
                    val_str = str(val) if val is not None else None

                # Validate param belongs to profile
                if not profile.parameters.filter(id=param_id).exists():
                    continue # Ignore invalid params
                
                if param_id in current_values:
                    rv = current_values[param_id]
                    rv.value = val_str
                    rv.save()
                else:
                    ReportValue.objects.create(
                        report=instance,
                        parameter_id=param_id,
                        value=val_str
                    )

        return Response({"status": "saved", "report_id": instance.id})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)

        if not instance:
             profile = self._get_profile(item)
             instance = ReportInstance.objects.create(
                 service_visit_item=item,
                 profile=profile,
                 created_by=request.user,
                 status="draft"
             )

        if instance.status in ["submitted", "verified"]:
             return Response({"status": "already_submitted"})

        # Validation
        profile = instance.profile
        required_params = profile.parameters.filter(is_required=True)
        existing_values = {str(v.parameter_id): v.value for v in instance.values.all()}
        
        missing = []
        for rp in required_params:
            param_id_str = str(rp.id)
            if param_id_str not in existing_values or not existing_values[param_id_str]:
                missing.append({
                    "parameter_id": param_id_str,
                    "message": "Required"
                })
        
        if missing:
            return Response({
                "error": "validation_failed", 
                "missing": missing
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            instance.status = "submitted"
            instance.save()
            
            # Update workflow status to PENDING_VERIFICATION
            item.status = "PENDING_VERIFICATION" 
            item.submitted_at = timezone.now()
            item.save()

        return Response({"status": "submitted"})
