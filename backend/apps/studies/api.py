from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Study, Visit, ReceiptSettings
from .serializers import StudySerializer, VisitSerializer, ReceiptSettingsSerializer

LEGACY_DEPRECATION_HEADERS = {
    "X-Deprecated": "true",
    "X-Deprecated-Reason": "Legacy studies/visits endpoints are deprecated. Use workflow service visits instead.",
    "X-Deprecated-Use": "/api/workflow/visits/",
}


def add_deprecation_headers(response):
    for key, value in LEGACY_DEPRECATION_HEADERS.items():
        response[key] = value
    return response

class StudyViewSet(viewsets.ModelViewSet):
    """
    LEGACY: Study model is deprecated. Use ServiceVisit workflow instead.
    Write operations (POST/PUT/PATCH/DELETE) are blocked for non-admin users.
    Read operations are allowed for backward compatibility.
    """
    queryset = Study.objects.select_related("patient","service","service__modality").all()
    serializer_class = StudySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["accession", "patient__name", "patient__mrn", "service__name"]
    filterset_fields = ["status", "service__modality__code", "service"]
    ordering_fields = ["created_at", "accession", "status"]

    def get_permissions(self):
        """Block write operations for non-admin users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return add_deprecation_headers(response)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return add_deprecation_headers(response)

    def create(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Study writes are deprecated. Use /api/workflow/visits/ to create service visits."
            },
            status=status.HTTP_410_GONE,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Study updates are deprecated. Use workflow item transitions instead."
            },
            status=status.HTTP_410_GONE,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Study updates are deprecated. Use workflow item transitions instead."
            },
            status=status.HTTP_410_GONE,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Study deletion is deprecated. Use workflow service visits instead."
            },
            status=status.HTTP_410_GONE,
        )

class VisitViewSet(viewsets.ModelViewSet):
    """
    LEGACY: Visit model is deprecated. Use ServiceVisit workflow instead.
    Write operations (POST/PUT/PATCH/DELETE) are blocked for non-admin users.
    Read operations are allowed for backward compatibility.
    """
    queryset = Visit.objects.select_related("patient", "created_by").prefetch_related("items__service", "items__service__modality").all()
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["visit_number", "patient__name", "patient__mrn"]
    filterset_fields = ["is_finalized", "patient"]
    ordering_fields = ["created_at", "visit_number"]
    
    def get_permissions(self):
        """Block write operations for non-admin users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'unified_intake', 'finalize']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return add_deprecation_headers(response)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return add_deprecation_headers(response)

    def create(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Visit writes are deprecated. Use /api/workflow/visits/create_visit/."
            },
            status=status.HTTP_410_GONE,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Visit updates are deprecated. Use workflow service visits instead."
            },
            status=status.HTTP_410_GONE,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Visit updates are deprecated. Use workflow service visits instead."
            },
            status=status.HTTP_410_GONE,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {
                "detail": "Legacy Visit deletion is deprecated. Use workflow service visits instead."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=False, methods=["post"], url_path="unified-intake")
    def unified_intake(self, request):
        """Unified endpoint for patient registration + exam registration + billing"""
        return Response(
            {
                "detail": "Legacy unified intake is deprecated. Use /api/workflow/visits/create_visit/."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        """Finalize a visit (lock billing and generate visit number if not already done)"""
        return Response(
            {
                "detail": "Legacy Visit finalization is deprecated. Use workflow service visits."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=True, methods=["post"], url_path="generate-receipt")
    def generate_receipt(self, request, pk=None):
        """Generate receipt number and PDF if not already generated"""
        return Response(
            {
                "detail": "Legacy receipt generation is deprecated. Use /api/pdf/{service_visit_id}/receipt/."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Get receipt PDF for printing/downloading"""
        return Response(
            {
                "detail": "Legacy receipt retrieval is deprecated. Use /api/pdf/{service_visit_id}/receipt/."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=True, methods=["get"], url_path="receipt-preview")
    def receipt_preview(self, request, pk=None):
        """Preview receipt HTML in browser (for testing/printing)"""
        return Response(
            {
                "detail": "Legacy receipt preview is deprecated. Use /api/pdf/{service_visit_id}/receipt/."
            },
            status=status.HTTP_410_GONE,
        )
    
    @action(detail=True, methods=["get"], url_path="usg-reports")
    def usg_reports(self, request, pk=None):
        """List all USG reports attached to this visit"""
        from apps.usg.models import UsgStudy
        from apps.usg.serializers import UsgStudySerializer
        
        visit = self.get_object()
        usg_studies = UsgStudy.objects.filter(visit=visit).select_related(
            'patient', 'template', 'created_by', 'verified_by', 'published_by'
        ).prefetch_related('field_values')
        
        serializer = UsgStudySerializer(usg_studies, many=True, context={'request': request})
        return Response(serializer.data)


class ReceiptSettingsViewSet(viewsets.ViewSet):
    """ViewSet for managing receipt branding settings (singleton)"""
    serializer_class = ReceiptSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Override to allow public access to public_settings action"""
        if self.action == 'public_settings':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def list(self, request):
        """Get current receipt settings"""
        settings_obj = ReceiptSettings.get_settings()
        serializer = self.serializer_class(settings_obj, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="public", permission_classes=[permissions.AllowAny])
    def public_settings(self, request):
        """Get public receipt settings (logo only, no auth required)"""
        settings_obj = ReceiptSettings.get_settings()
        data = {
            "logo_image_url": None,
            "header_text": settings_obj.header_text if settings_obj else "Consultant Place Clinics",
        }
        if settings_obj and settings_obj.logo_image:
            data["logo_image_url"] = request.build_absolute_uri(settings_obj.logo_image.url)
        return Response(data)
    
    def retrieve(self, request, pk=None):
        """Get current receipt settings (same as list for singleton)"""
        settings_obj = ReceiptSettings.get_settings()
        serializer = self.serializer_class(settings_obj, context={"request": request})
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """Update receipt settings (partial update supported)"""
        settings_obj = ReceiptSettings.get_settings()
        serializer = self.serializer_class(settings_obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Partial update receipt settings"""
        return self.update(request, pk)
    
    @action(detail=False, methods=["post"], url_path="logo")
    def upload_logo(self, request):
        """Upload logo image"""
        settings_obj = ReceiptSettings.get_settings()
        if "logo_image" not in request.FILES:
            return Response({"error": "logo_image file is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        settings_obj.logo_image = request.FILES["logo_image"]
        settings_obj.updated_by = request.user
        settings_obj.save()
        
        serializer = self.get_serializer(settings_obj, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["post"], url_path="header-image")
    def upload_header_image(self, request):
        """Upload header image"""
        settings_obj = ReceiptSettings.get_settings()
        if "header_image" not in request.FILES:
            return Response({"error": "header_image file is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        settings_obj.header_image = request.FILES["header_image"]
        settings_obj.updated_by = request.user
        settings_obj.save()
        
        serializer = self.get_serializer(settings_obj, context={"request": request})
        return Response(serializer.data)
