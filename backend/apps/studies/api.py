from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
import os
from pathlib import Path
from .models import Study, Visit, OrderItem, ReceiptSequence, ReceiptSettings
from .serializers import StudySerializer, VisitSerializer, OrderItemSerializer, UnifiedIntakeSerializer, ReceiptSettingsSerializer

class StudyViewSet(viewsets.ModelViewSet):
    queryset = Study.objects.select_related("patient","service","service__modality").all()
    serializer_class = StudySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["accession", "patient__name", "patient__mrn", "service__name"]
    filterset_fields = ["status", "service__modality__code", "service"]
    ordering_fields = ["created_at", "accession", "status"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.select_related("patient", "created_by").prefetch_related("items__service", "items__service__modality").all()
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["visit_number", "patient__name", "patient__mrn"]
    filterset_fields = ["is_finalized", "patient"]
    ordering_fields = ["created_at", "visit_number"]
    
    @action(detail=False, methods=["post"], url_path="unified-intake")
    def unified_intake(self, request):
        """Unified endpoint for patient registration + exam registration + billing"""
        serializer = UnifiedIntakeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            visit = serializer.save()
            visit.is_finalized = True
            visit.finalized_at = timezone.now()
            visit.save()
            
            response_serializer = VisitSerializer(visit, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize(self, request, pk=None):
        """Finalize a visit (lock billing and generate visit number if not already done)"""
        visit = self.get_object()
        if visit.is_finalized:
            return Response({"detail": "Visit already finalized"}, status=status.HTTP_400_BAD_REQUEST)
        
        visit.is_finalized = True
        visit.finalized_at = timezone.now()
        visit.save()
        
        serializer = self.get_serializer(visit)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="generate-receipt")
    def generate_receipt(self, request, pk=None):
        """Generate receipt number and PDF if not already generated"""
        visit = self.get_object()
        
        # If receipt already generated, return existing
        if visit.receipt_number and visit.receipt_pdf_path:
            serializer = self.get_serializer(visit)
            return Response(serializer.data)
        
        # Generate receipt number
        if not visit.receipt_number:
            visit.receipt_number = ReceiptSequence.get_next_receipt_number()
        
        # Generate PDF
        from apps.reporting.pdf import build_receipt_pdf
        pdf_file = build_receipt_pdf(visit)
        
        # Save PDF to storage
        now = timezone.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs" / "receipts" / year / month
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"{visit.receipt_number}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        
        # Store relative path
        visit.receipt_pdf_path = f"pdfs/receipts/{year}/{month}/{pdf_filename}"
        visit.receipt_generated_at = timezone.now()
        visit.save()
        
        serializer = self.get_serializer(visit)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Get receipt PDF for printing/downloading"""
        visit = self.get_object()
        
        # If PDF exists, serve it
        if visit.receipt_pdf_path:
            pdf_path = Path(settings.MEDIA_ROOT) / visit.receipt_pdf_path
            if pdf_path.exists():
                with open(pdf_path, "rb") as f:
                    response = HttpResponse(f.read(), content_type="application/pdf")
                    filename = visit.receipt_number or visit.visit_number
                    response["Content-Disposition"] = f'inline; filename="receipt_{filename}.pdf"'
                    return response
        
        # Otherwise generate on-the-fly (for backward compatibility)
        # Generate receipt number if not exists
        if not visit.receipt_number:
            visit.receipt_number = ReceiptSequence.get_next_receipt_number()
            visit.save()
        
        # Generate PDF
        from apps.reporting.pdf import build_receipt_pdf
        pdf_file = build_receipt_pdf(visit)
        
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        filename = visit.receipt_number or visit.visit_number
        response["Content-Disposition"] = f'inline; filename="receipt_{filename}.pdf"'
        return response


class ReceiptSettingsViewSet(viewsets.ViewSet):
    """ViewSet for managing receipt branding settings (singleton)"""
    serializer_class = ReceiptSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get current receipt settings"""
        settings_obj = ReceiptSettings.get_settings()
        serializer = self.serializer_class(settings_obj, context={"request": request})
        return Response(serializer.data)
    
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
