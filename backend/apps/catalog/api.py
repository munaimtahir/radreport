import csv
import io
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from .models import Modality, Service
from .serializers import ModalitySerializer, ServiceSerializer
class ModalityViewSet(viewsets.ModelViewSet):
    queryset = Modality.objects.all()
    serializer_class = ModalitySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["code", "name"]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("modality").filter(is_active=True)
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

                        if category not in dict(Service.CATEGORY_CHOICES):
                            raise ValueError(f"Invalid category '{category}'")
                        if tat_unit not in dict(Service.TAT_UNIT_CHOICES):
                            raise ValueError(f"Invalid tat_unit '{tat_unit}'")
                        
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

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        """Export services to CSV."""
        include_inactive = request.query_params.get("include_inactive") == "true"
        services = Service.objects.select_related("modality")
        if not include_inactive:
            services = services.filter(is_active=True)

        fieldnames = ["code", "name", "category", "modality", "charges", "tat_value", "tat_unit", "active"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for service in services.order_by("name"):
            writer.writerow({
                "code": service.code or "",
                "name": service.name,
                "category": service.category,
                "modality": service.modality.code if service.modality else "",
                "charges": service.charges,
                "tat_value": service.tat_value,
                "tat_unit": service.tat_unit,
                "active": "true" if service.is_active else "false",
            })

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="services_export.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="template-csv")
    def template_csv(self, request):
        """Download CSV template for services import."""
        fieldnames = ["code", "name", "category", "modality", "charges", "tat_value", "tat_unit", "active"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "code": "SRV-001",
            "name": "Example Service",
            "category": "Radiology",
            "modality": "USG",
            "charges": "0",
            "tat_value": "1",
            "tat_unit": "hours",
            "active": "true",
        })
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="services_template.csv"'
        return response
    
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
        ).select_related('modality')

        
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
