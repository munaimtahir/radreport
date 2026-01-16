import csv
import io
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
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

    @action(detail=True, methods=["get", "post"], url_path="templates", permission_classes=[permissions.IsAuthenticated])
    def manage_templates(self, request, pk=None):
        """List or attach templates to a service. GET lists, POST attaches."""
        if request.method == "GET":
            links = ServiceReportTemplate.objects.filter(service_id=pk).select_related("template", "service")
            serializer = ServiceReportTemplateSerializer(links, many=True)
            return Response(serializer.data)
        else:  # POST
            # Admin-only for POST
            if not request.user.is_staff:
                return Response(
                    {"detail": "You do not have permission to perform this action."},
                    status=status.HTTP_403_FORBIDDEN
                )
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
        # Check if is_default was provided before saving
        is_default_provided = "is_default" in serializer.validated_data
        is_default_value = serializer.validated_data.get("is_default", False)
        serializer.save()
        # Use the saved instance's value, but only act if is_default was explicitly provided
        if is_default_provided and link.is_default:
            ServiceReportTemplate.objects.filter(service_id=pk).exclude(id=link.id).update(is_default=False)
        return Response(ServiceReportTemplateSerializer(link).data)

    @action(detail=True, methods=["delete"], url_path="templates/(?P<link_id>[^/.]+)", permission_classes=[permissions.IsAdminUser])
    def delete_template_link(self, request, pk=None, link_id=None):
        link = get_object_or_404(ServiceReportTemplate, service_id=pk, id=link_id)
        was_default = link.is_default
        link.is_active = False
        link.is_default = False
        link.save(update_fields=["is_active", "is_default"])
        
        # If we just deleted the default template, promote the most recent active link to default
        if was_default:
            new_default = ServiceReportTemplate.objects.filter(
                service_id=pk, is_active=True
            ).order_by("-created_at").first()
            if new_default:
                new_default.is_default = True
                new_default.save(update_fields=["is_default"])
        
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
        Return top 5 most used services based on service visit items.
        
        Note: This query uses Count aggregation which scans service_visit_items.
        For large databases, consider adding an index on the service foreign key
        in ServiceVisitItem (which should already exist) or implementing a 
        denormalized counter if performance becomes an issue.
        """
        queryset = Service.objects.filter(is_active=True).annotate(
            usage_count=Count("service_visit_items")
        ).order_by("-usage_count", "name")[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
