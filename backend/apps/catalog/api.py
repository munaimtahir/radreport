import csv
import io
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Modality, Service
from .serializers import ModalitySerializer, ServiceSerializer
from apps.templates.models import ServiceReportTemplate
from apps.templates.serializers import ServiceReportTemplateSerializer

class ModalityViewSet(viewsets.ModelViewSet):
    queryset = Modality.objects.all()
    serializer_class = ModalitySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["code", "name"]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("modality", "default_template").filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "modality__code", "code"]
    ordering_fields = ["name", "price", "tat_minutes"]
    filterset_fields = ["category", "modality", "is_active"]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by active by default, but allow showing all if requested
        if self.request.query_params.get("include_inactive") != "true":
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def perform_create(self, serializer):
        """Set user context for audit logging"""
        instance = serializer.save()
        instance._current_user = self.request.user
        instance.save()
    
    def perform_update(self, serializer):
        """Set user context for audit logging"""
        instance = serializer.save()
        instance._current_user = self.request.user
        instance.save()

    @action(detail=True, methods=["get"], url_path="templates")
    def list_templates(self, request, pk=None):
        links = ServiceReportTemplate.objects.filter(service_id=pk).select_related("template", "service")
        serializer = ServiceReportTemplateSerializer(links, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="templates", permission_classes=[permissions.IsAdminUser])
    def attach_template(self, request, pk=None):
        serializer = ServiceReportTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template_id = serializer.validated_data["template_id"]
        link, _ = ServiceReportTemplate.objects.update_or_create(
            service_id=pk,
            template_id=template_id,
            defaults={
                "is_default": serializer.validated_data.get("is_default", False),
                "is_active": serializer.validated_data.get("is_active", True),
            },
        )
        if link.is_default:
            ServiceReportTemplate.objects.filter(service_id=pk).exclude(id=link.id).update(is_default=False)
        return Response(ServiceReportTemplateSerializer(link).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="templates/(?P<link_id>[^/.]+)", permission_classes=[permissions.IsAdminUser])
    def update_template_link(self, request, pk=None, link_id=None):
        link = get_object_or_404(ServiceReportTemplate, service_id=pk, id=link_id)
        serializer = ServiceReportTemplateSerializer(link, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if serializer.validated_data.get("is_default"):
            ServiceReportTemplate.objects.filter(service_id=pk).exclude(id=link.id).update(is_default=False)
        return Response(ServiceReportTemplateSerializer(link).data)

    @action(detail=True, methods=["delete"], url_path="templates/(?P<link_id>[^/.]+)", permission_classes=[permissions.IsAdminUser])
    def delete_template_link(self, request, pk=None, link_id=None):
        link = get_object_or_404(ServiceReportTemplate, service_id=pk, id=link_id)
        link.is_active = False
        link.is_default = False
        link.save(update_fields=["is_active", "is_default"])
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        """Import services from CSV file"""
        if "file" not in request.FILES:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES["file"]
        if not file.name.endswith(".csv"):
            return Response({"detail": "File must be a CSV"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            decoded_file = file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            required_columns = ["code", "name", "category", "modality", "charges", "tat_value", "tat_unit", "active"]
            if not all(col in reader.fieldnames for col in required_columns):
                return Response(
                    {"detail": f"CSV must contain columns: {', '.join(required_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_count = 0
            updated_count = 0
            errors = []
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        code = row["code"].strip()
                        name = row["name"].strip()
                        category = row["category"].strip()
                        modality_code = row["modality"].strip().upper()
                        charges = float(row["charges"].strip())
                        tat_value = int(row["tat_value"].strip())
                        tat_unit = row["tat_unit"].strip().lower()
                        is_active = row["active"].strip().lower() in ["true", "1", "yes"]
                        
                        # Get or create modality
                        modality, _ = Modality.objects.get_or_create(
                            code=modality_code,
                            defaults={"name": modality_code}
                        )
                        
                        # Get or create service by code
                        service, created = Service.objects.get_or_create(
                            code=code,
                            defaults={
                                "modality": modality,
                                "name": name,
                                "category": category,
                                "charges": charges,
                                "price": charges,
                                "tat_value": tat_value,
                                "tat_unit": tat_unit,
                                "is_active": is_active,
                            }
                        )
                        if created:
                            service._current_user = request.user
                            service.save()
                        
                        if not created:
                            # Update existing service
                            service._current_user = request.user
                            service.modality = modality
                            service.name = name
                            service.category = category
                            service.charges = charges
                            service.price = charges
                            service.tat_value = tat_value
                            service.tat_unit = tat_unit
                            service.is_active = is_active
                            service.save()
                            updated_count += 1
                        else:
                            created_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
            
            result = {
                "created": created_count,
                "updated": updated_count,
                "errors": errors if errors else None,
            }
            
            if errors:
                return Response(result, status=status.HTTP_207_MULTI_STATUS)
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["get"], url_path="most-used")
    def most_used(self, request):
        """
        Get most frequently used services.
        Returns top services by usage count (based on ServiceVisitItem records).
        
        Query params:
        - limit: Number of services to return (default: 5)
        """
        limit = int(request.query_params.get("limit", 5))
        
        # Count usage from ServiceVisitItem (workflow) and OrderItem (legacy)
        from apps.workflow.models import ServiceVisitItem
        from apps.studies.models import OrderItem
        
        # Count from ServiceVisitItem
        workflow_counts = ServiceVisitItem.objects.values('service_id').annotate(
            count=Count('id')
        ).values('service_id', 'count')
        
        # Count from OrderItem (legacy)
        legacy_counts = OrderItem.objects.values('service_id').annotate(
            count=Count('id')
        ).values('service_id', 'count')
        
        # Combine counts
        usage_map = {}
        for item in workflow_counts:
            service_id = item['service_id']
            usage_map[service_id] = usage_map.get(service_id, 0) + item['count']
        
        for item in legacy_counts:
            service_id = item['service_id']
            usage_map[service_id] = usage_map.get(service_id, 0) + item['count']
        
        # Get services with usage counts, sorted by usage
        service_ids = sorted(usage_map.keys(), key=lambda x: usage_map[x], reverse=True)[:limit]
        
        # Fetch services
        services = Service.objects.filter(
            id__in=service_ids,
            is_active=True
        ).select_related('modality', 'default_template')
        
        # Create a map for ordering
        service_map = {str(s.id): s for s in services}
        ordered_services = [service_map[str(sid)] for sid in service_ids if str(sid) in service_map]
        
        # Serialize with usage_count
        serializer = self.get_serializer(ordered_services, many=True)
        data = serializer.data
        
        # Add usage_count to each service
        for item in data:
            service_id = item['id']
            item['usage_count'] = usage_map.get(service_id, 0)
        
        return Response(data)
