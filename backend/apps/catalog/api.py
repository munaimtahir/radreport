import csv
import io
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Count
from .models import Modality, Service
from .serializers import ModalitySerializer, ServiceSerializer

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
        """Return top 5 most used services based on service visit items."""
        queryset = Service.objects.filter(is_active=True).annotate(
            usage_count=Count("service_visit_items")
        ).order_by("-usage_count", "name")[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
