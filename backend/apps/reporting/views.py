from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from rest_framework import viewsets, status, exceptions, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.workflow.models import ServiceVisitItem, ServiceVisit
from .models import (
    ServiceReportProfile, ReportInstance, ReportValue,
    ReportProfile, ReportParameter, ReportParameterOption
)
from .serializers import (
    ReportProfileSerializer, ReportInstanceSerializer, ReportValueSerializer, ReportSaveSerializer,
    ReportParameterSerializer, ServiceReportProfileSerializer
)
from .services.narrative_v1 import generate_report_narrative
from .pdf_engine.report_pdf import generate_report_pdf
from .models import ReportPublishSnapshot, ReportActionLog
import hashlib
import json
from django.core.files.base import ContentFile

class ReportProfileViewSet(viewsets.ModelViewSet):
    queryset = ReportProfile.objects.all()
    serializer_class = ReportProfileSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    search_fields = ["code", "name", "modality"]
    filterset_fields = ["modality", "is_active"]

class ReportParameterViewSet(viewsets.ModelViewSet):
    queryset = ReportParameter.objects.all()
    serializer_class = ReportParameterSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ["profile", "section"]
    ordering_fields = ["order"]

    def perform_create(self, serializer):
        instance = serializer.save()
        self._handle_options(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._handle_options(instance)

    def _handle_options(self, instance):
        options_data = self.request.data.get("options")
        if options_data is not None and isinstance(options_data, list):
            with transaction.atomic():
                # Replace options logic: delete existing and create new?
                # Or smart update? For simplicity, delete and recreate since IDs might be temp
                # But we should preserve IDs if possible?
                # The frontend sends "id" if existing.

                existing_ids = [opt.get("id") for opt in options_data if opt.get("id")]
                # Delete those not in list
                instance.options.exclude(id__in=existing_ids).delete()

                for opt in options_data:
                    oid = opt.get("id")
                    label = opt.get("label", "")
                    value = opt.get("value", "")
                    order = opt.get("order", 0)

                    if oid:
                        # Fix IDOR: scope update to instance's options only
                        instance.options.filter(id=oid).update(
                            label=label, value=value, order=order
                        )
                    else:
                        ReportParameterOption.objects.create(
                            parameter=instance,
                            label=label,
                            value=value,
                            order=order
                        )

class ServiceReportProfileViewSet(viewsets.ModelViewSet):
    queryset = ServiceReportProfile.objects.all()
    serializer_class = ServiceReportProfileSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ["service", "profile"]

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
            "is_published": instance.is_published,
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
            
            # Create a map of existing values: ID -> ReportValue obj
            # ID is either parameter.id or profile_link.id
            current_values = {}
            for v in instance.values.all():
                if v.parameter_id:
                    current_values[str(v.parameter_id)] = v
                if v.profile_link_id:
                    current_values[str(v.profile_link_id)] = v
            
            # Pre-fetch valid IDs for validation
            valid_param_ids = set(str(p.id) for p in profile.parameters.all())
            valid_link_ids = set(str(l.id) for l in profile.library_links.all())

            for item_data in values_list:
                param_id = str(item_data["parameter_id"])
                val = item_data["value"]
                
                # val might be list or string, save as string/JSON
                if isinstance(val, (list, dict)):
                    import json
                    val_str = json.dumps(val)
                else:
                    val_str = str(val) if val is not None else None

                # Determine type
                if param_id in valid_param_ids:
                    is_legacy = True
                elif param_id in valid_link_ids:
                    is_legacy = False
                else:
                    continue # Ignore invalid params
                
    
                if param_id in current_values:
                    rv = current_values[param_id]
                    rv.value = val_str
                    rv.save()
                else:
                    if is_legacy:
                        ReportValue.objects.create(
                            report=instance,
                            parameter_id=param_id,
                            value=val_str
                        )
                    else:
                        ReportValue.objects.create(
                            report=instance,
                            profile_link_id=param_id,
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
        required_links = profile.library_links.filter(is_required=True)
        
        existing_values = {}
        for v in instance.values.all():
            val = v.value
            if v.parameter_id:
                existing_values[str(v.parameter_id)] = val
            if v.profile_link_id:
                existing_values[str(v.profile_link_id)] = val
        
        missing = []
        # Check legacy
        for rp in required_params:
            param_id_str = str(rp.id)
            if param_id_str not in existing_values or not existing_values[param_id_str]:
                missing.append({
                    "parameter_id": param_id_str,
                    "message": "Required"
                })
        # Check links
        for rl in required_links:
            link_id_str = str(rl.id)
            if link_id_str not in existing_values or not existing_values[link_id_str]:
                missing.append({
                    "parameter_id": link_id_str,
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

    @action(detail=True, methods=["post"], url_path="generate-narrative")
    def generate_narrative(self, request, pk=None):
        """
        Generates and saves the narrative.
        """
        item = self._get_item(pk)
        instance = self._get_instance(item)

        if not instance:
            raise exceptions.NotFound("Report must be started (saved as draft) before generating narrative.")

        # Logic per requirements: 
        # Allowed when report exists (draft or submitted).
        # We allow re-generation even if submitted/verified? 
        # Requirement: "When reportStatus is submitted/verified: Read-only already; still allow Generate Preview only if permitted (optional)"
        # Let's allow it. It updates the narrative fields in the DB.
        
        narrative_data = generate_report_narrative(str(instance.id))
        
        with transaction.atomic():
            instance.findings_text = narrative_data["findings_text"]
            instance.impression_text = narrative_data["impression_text"]
            instance.limitations_text = narrative_data["limitations_text"]
            instance.narrative_version = narrative_data["version"]
            instance.narrative_updated_at = timezone.now()
            instance.save()
            
        return Response({
            "status": instance.status,
            "narrative": narrative_data
        })

    @action(detail=True, methods=["get"], url_path="narrative")
    def narrative(self, request, pk=None):
        """
        Returns stored narrative fields.
        """
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
            return Response({
                "status": "draft",
                "narrative": {
                    "version": "v1",
                    "findings_text": "",
                    "impression_text": "",
                    "limitations_text": ""
                }
            })
            
        return Response({
            "status": instance.status,
            "narrative": {
                "version": instance.narrative_version,
                "findings_text": instance.findings_text or "",
                "impression_text": instance.impression_text or "",
                "limitations_text": instance.limitations_text or ""
            }
        })
    @action(detail=True, methods=["get"], url_path="report-pdf")
    def report_pdf(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report has not been started.")
             
        # Check permission? IsAuthenticated is on class.
        # User asked for "Read-only access allowed for submitted/verified reports"
        # "Draft allowed if explicitly requested (same endpoint)"
        # Since it is a GET request, it is read-only by definition.
        
        # Auto-generate narrative if empty?
        # Requirement: "If narrative not generated yet: Auto-generate narrative using Stage 2 engine; Persist it"
        if not instance.narrative_updated_at or not instance.findings_text:
             narrative_data = generate_report_narrative(str(instance.id))
             with transaction.atomic():
                instance.findings_text = narrative_data["findings_text"]
                instance.impression_text = narrative_data["impression_text"]
                instance.limitations_text = narrative_data["limitations_text"]
                instance.narrative_version = narrative_data["version"]
                instance.narrative_updated_at = timezone.now()
                instance.save()
        
        try:
            pdf_bytes = generate_report_pdf(str(instance.id))
        except Exception as e:
            # Log error?
            return Response({"error": f"Failed to generate PDF: {str(e)}"}, status=500)
            
        filename = f"Report_{item.service_visit.visit_id}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        # Content-Disposition: inline; filename="..."
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=["post"], url_path="return-for-correction")
    def return_for_correction(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
            raise exceptions.NotFound("Report not found.")
            
        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can return reports.")

        # Logic: Allowed only if submitted or verified
        if instance.status not in ["submitted", "verified"]:
            return Response({"error": "Report can only be returned if submitted or verified."}, status=409)

        reason = request.data.get("reason", "").strip()
        if not reason:
             return Response({"error": "Reason is required."}, status=400)

        with transaction.atomic():
            instance.status = "draft"
            instance.save()
            
            # Update workflow status if possible
            item.status = "RETURNED_FOR_CORRECTION"
            item.save()
            
            ReportActionLog.objects.create(
                report=instance,
                action="return",
                actor=request.user,
                meta={"reason": reason}
            )

        return Response({"status": "returned"})

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report not found.")

        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can verify reports.")

        if instance.status != "submitted":
             return Response({"error": "Only submitted reports can be verified."}, status=409)

        notes = request.data.get("notes", "")

        with transaction.atomic():
            # Ensure narrative exists
            if not instance.findings_text:
                narrative_data = generate_report_narrative(str(instance.id))
                instance.findings_text = narrative_data["findings_text"]
                instance.impression_text = narrative_data["impression_text"]
                instance.limitations_text = narrative_data["limitations_text"]
                instance.narrative_version = narrative_data["version"]
                instance.narrative_updated_at = timezone.now()
            
            instance.status = "verified"
            instance.save()
            
            # Log action
            ReportActionLog.objects.create(
                report=instance,
                action="verify",
                actor=request.user,
                meta={"notes": notes}
            )
            
        return Response({"status": "verified"})

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report not found.")

        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can publish reports.")

        if instance.status != "verified":
             return Response({"error": "Only verified reports can be published."}, status=409)

        notes = request.data.get("notes", "")

        with transaction.atomic():
            # Ensure narrative exists (should be there from verify, but double check)
            if not instance.findings_text:
                narrative_data = generate_report_narrative(str(instance.id))
                instance.findings_text = narrative_data["findings_text"]
                instance.impression_text = narrative_data["impression_text"]
                instance.limitations_text = narrative_data["limitations_text"]
                instance.narrative_version = narrative_data["version"]
                instance.narrative_updated_at = timezone.now()
                instance.save() # Save narrative parts first so PDF gen picks them up? 
                # generate_report_pdf reads from DB usually, so we need to save instance first or pass data. 
                # looking at pdf_engine/report_pdf, it takes report_id. So we MUST save instance first.
            
            # Calculate next version
            last_snapshot = instance.publish_snapshots.order_by("-version").first()
            version = (last_snapshot.version + 1) if last_snapshot else 1

            # Generate JSON map
            # We want FULL map including defaults? Prompt says: "values_json = FULL map of all parameters in profile (including defaults) keyed by parameter_id"
            # We'll rely on what's in DB + what's not in DB but in profile?
            # Ideally we iterate profile parameters
            values_map = {}
            # Get all existing values
            existing_values = {str(v.parameter_id): v.value for v in instance.values.all()}
            
            # Get all parameters from profile
            for param in instance.profile.parameters.all():
                p_id = str(param.id)
                val = existing_values.get(p_id)
                if val is None:
                    val = param.normal_value # Use default/normal if missing? Prompt says "including defaults". 
                    # Note: ReportParameter has 'normal_value'.
                values_map[p_id] = val
            
            # Canonical JSON for hash
            canonical_json = json.dumps(values_map, sort_keys=True)
            narrative_concat = (instance.findings_text or "") + (instance.impression_text or "") + (instance.limitations_text or "")
            hash_input = canonical_json + narrative_concat
            sha256_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

            # Generate PDF
            pdf_bytes = generate_report_pdf(str(instance.id))
            file_name = f"Report_{item.service_visit.visit_id}_v{version}.pdf"
            
            snapshot = ReportPublishSnapshot(
                report=instance,
                version=version,
                published_by=request.user,
                findings_text=instance.findings_text or "",
                impression_text=instance.impression_text or "",
                limitations_text=instance.limitations_text or "",
                values_json=values_map, # This stores dictionary, Django JSONField handles it
                sha256=sha256_hash,
                notes=notes
            )
            snapshot.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
            snapshot.save()

            # Update workflow status
            item.status = "PUBLISHED"
            item.published_at = timezone.now()
            item.save()

            ReportActionLog.objects.create(
                report=instance,
                action="publish",
                actor=request.user,
                meta={"version": version, "sha256": sha256_hash, "notes": notes}
            )

        return Response({"status": "published", "version": version})

    @action(detail=True, methods=["get"], url_path="publish-history")
    def publish_history(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        if not instance:
             return Response([])
        
        snapshots = instance.publish_snapshots.all().order_by("-version")
        history = []
        for snap in snapshots:
            history.append({
                "version": snap.version,
                "published_at": snap.published_at,
                "published_by": snap.published_by.username if snap.published_by else "Unknown",
                "sha256": snap.sha256,
                "notes": snap.notes,
                "pdf_url": request.build_absolute_uri(snap.pdf_file.url) if snap.pdf_file else None
            })
        return Response(history)

    @action(detail=True, methods=["get"], url_path="published-pdf")
    def published_pdf(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        if not instance:
             raise exceptions.NotFound("Report not found.")
        
        version = request.query_params.get("version")
        if not version:
             return Response({"error": "Version required"}, status=400)
             
        try:
            snapshot = instance.publish_snapshots.get(version=version)
        except ReportPublishSnapshot.DoesNotExist:
             raise exceptions.NotFound("Snapshot not found.")
             
        if not snapshot.pdf_file:
             raise exceptions.NotFound("PDF file missing for this snapshot.")

        # Return file response
        response = HttpResponse(snapshot.pdf_file.read(), content_type='application/pdf')
        filename = f"Report_{item.service_visit.visit_id}_v{version}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
