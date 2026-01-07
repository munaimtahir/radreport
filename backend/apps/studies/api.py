from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from .models import Study, Visit, OrderItem
from .serializers import StudySerializer, VisitSerializer, OrderItemSerializer, UnifiedIntakeSerializer

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
    
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Generate receipt PDF for printing"""
        visit = self.get_object()
        
        # Generate PDF
        from apps.reporting.pdf import build_receipt_pdf
        pdf_file = build_receipt_pdf(visit)
        
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="receipt_{visit.visit_number}.pdf"'
        return response
