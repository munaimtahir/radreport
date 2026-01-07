from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from pathlib import Path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    ServiceCatalog, ServiceVisit, Invoice, Payment,
    USGReport, OPDVitals, OPDConsult, StatusAuditLog
)
from .serializers import (
    ServiceCatalogSerializer, ServiceVisitSerializer, InvoiceSerializer,
    PaymentSerializer, USGReportSerializer, OPDVitalsSerializer,
    OPDConsultSerializer, ServiceVisitCreateSerializer, StatusTransitionSerializer
)
from .permissions import (
    IsRegistrationDesk, IsPerformanceDesk, IsVerificationDesk,
    IsRegistrationOrPerformanceDesk, IsPerformanceOrVerificationDesk, IsAnyDesk
)
from apps.patients.models import Patient
try:
    from apps.studies.models import ReceiptSequence
except ImportError:
    # Fallback if ReceiptSequence doesn't exist
    class ReceiptSequence:
        @staticmethod
        def get_next_receipt_number():
            from django.utils import timezone
            now = timezone.now()
            yymm = now.strftime("%y%m")
            # Simple fallback - in production use proper sequence
            return f"{yymm}-001"


class ServiceCatalogViewSet(viewsets.ModelViewSet):
    """Service catalog management"""
    queryset = ServiceCatalog.objects.filter(is_active=True)
    serializer_class = ServiceCatalogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["code", "name"]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "code"]


class ServiceVisitViewSet(viewsets.ModelViewSet):
    """Service visit management"""
    queryset = ServiceVisit.objects.select_related("patient", "service", "created_by", "assigned_to").prefetch_related("status_audit_logs__changed_by").all()
    serializer_class = ServiceVisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["visit_id", "patient__name", "patient__patient_reg_no", "patient__mrn", "service__name"]
    filterset_fields = ["status", "service"]
    ordering_fields = ["registered_at", "visit_id", "status"]
    
    def get_queryset(self):
        """Filter by workflow and status if provided"""
        queryset = super().get_queryset()
        workflow = self.request.query_params.get("workflow", None)
        status_filter = self.request.query_params.get("status", None)
        
        if workflow:
            if workflow == "USG":
                queryset = queryset.filter(service__code="USG")
            elif workflow == "OPD":
                queryset = queryset.filter(service__code="OPD")
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=["post"], permission_classes=[IsRegistrationDesk])
    def create_visit(self, request):
        """Create service visit at registration desk"""
        serializer = ServiceVisitCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            service_visit = serializer.save()
            response_serializer = ServiceVisitSerializer(service_visit, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"], permission_classes=[IsAnyDesk])
    def transition_status(self, request, pk=None):
        """Transition service visit status with audit logging"""
        service_visit = self.get_object()
        serializer = StatusTransitionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        to_status = serializer.validated_data["to_status"]
        reason = serializer.validated_data.get("reason", "")
        from_status = service_visit.status
        
        # Validate transition
        valid_transitions = {
            "REGISTERED": ["IN_PROGRESS", "CANCELLED"],
            "IN_PROGRESS": ["PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION", "CANCELLED"],
            "PENDING_VERIFICATION": ["PUBLISHED", "RETURNED_FOR_CORRECTION", "CANCELLED"],
            "RETURNED_FOR_CORRECTION": ["IN_PROGRESS", "CANCELLED"],
            "PUBLISHED": [],  # No transitions from published
            "CANCELLED": [],  # No transitions from cancelled
        }
        
        if to_status not in valid_transitions.get(from_status, []):
            return Response(
                {"detail": f"Invalid transition from {from_status} to {to_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform transition
        with transaction.atomic():
            service_visit.status = to_status
            service_visit.save()
            
            # Log transition
            StatusAuditLog.objects.create(
                service_visit=service_visit,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                changed_by=request.user,
            )
        
        response_serializer = ServiceVisitSerializer(service_visit, context={"request": request})
        return Response(response_serializer.data)


class USGReportViewSet(viewsets.ModelViewSet):
    """USG report management"""
    queryset = USGReport.objects.select_related("service_visit", "created_by", "updated_by", "verifier").all()
    serializer_class = USGReportSerializer
    permission_classes = [IsPerformanceOrVerificationDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(service_visit_id=visit_id)
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            return self.queryset.get(service_visit_id=visit_id)
        except USGReport.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("USG report not found for this visit")
    
    def create(self, request):
        """Create or update USG report"""
        visit_id = request.data.get("visit_id") or request.query_params.get("visit_id")
        if not visit_id:
            return Response({"detail": "visit_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service_visit = ServiceVisit.objects.get(id=visit_id)
        except ServiceVisit.DoesNotExist:
            return Response({"detail": "Service visit not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if report exists
        report, created = USGReport.objects.get_or_create(
            service_visit=service_visit,
            defaults={
                "created_by": request.user,
                "updated_by": request.user,
            }
        )
        
        if not created:
            report.updated_by = request.user
            report.report_json = request.data.get("report_json", report.report_json)
            report.save()
        
        serializer = self.get_serializer(report, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"], permission_classes=[IsPerformanceDesk])
    def save_draft(self, request, pk=None):
        """Save USG report draft"""
        report = self.get_object()
        report.report_json = request.data.get("report_json", {})
        report.updated_by = request.user
        report.save()
        
        # Transition to IN_PROGRESS if still REGISTERED
        if report.service_visit.status == "REGISTERED":
            report.service_visit.status = "IN_PROGRESS"
            report.service_visit.save()
            StatusAuditLog.objects.create(
                service_visit=report.service_visit,
                from_status="REGISTERED",
                to_status="IN_PROGRESS",
                changed_by=request.user,
            )
        
        serializer = self.get_serializer(report, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], permission_classes=[IsPerformanceDesk])
    def submit_for_verification(self, request, pk=None):
        """Submit USG report for verification"""
        report = self.get_object()
        report.report_json = request.data.get("report_json", report.report_json)
        report.updated_by = request.user
        report.save()
        
        # Transition to PENDING_VERIFICATION
        service_visit = report.service_visit
        from_status = service_visit.status
        service_visit.status = "PENDING_VERIFICATION"
        service_visit.save()
        
        StatusAuditLog.objects.create(
            service_visit=service_visit,
            from_status=from_status,
            to_status="PENDING_VERIFICATION",
            changed_by=request.user,
        )
        
        serializer = self.get_serializer(report, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], permission_classes=[IsVerificationDesk])
    def publish(self, request, pk=None):
        """Publish USG report (verification desk)"""
        report = self.get_object()
        service_visit = report.service_visit
        
        if service_visit.status != "PENDING_VERIFICATION":
            return Response(
                {"detail": "Report must be in PENDING_VERIFICATION status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate PDF
        from .pdf import build_usg_report_pdf
        pdf_file = build_usg_report_pdf(report)
        
        # Save PDF
        now = timezone.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs" / "reports" / "usg" / year / month
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"{service_visit.visit_id}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        
        # Update report
        report.published_pdf_path = f"pdfs/reports/usg/{year}/{month}/{pdf_filename}"
        report.verifier = request.user
        report.verified_at = timezone.now()
        report.save()
        
        # Transition to PUBLISHED
        service_visit.status = "PUBLISHED"
        service_visit.save()
        
        StatusAuditLog.objects.create(
            service_visit=service_visit,
            from_status="PENDING_VERIFICATION",
            to_status="PUBLISHED",
            changed_by=request.user,
        )
        
        serializer = self.get_serializer(report, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], permission_classes=[IsVerificationDesk])
    def return_for_correction(self, request, pk=None):
        """Return USG report for correction"""
        report = self.get_object()
        reason = request.data.get("reason", "")
        
        report.return_reason = reason
        report.save()
        
        # Transition to RETURNED_FOR_CORRECTION
        service_visit = report.service_visit
        from_status = service_visit.status
        service_visit.status = "RETURNED_FOR_CORRECTION"
        service_visit.save()
        
        StatusAuditLog.objects.create(
            service_visit=service_visit,
            from_status=from_status,
            to_status="RETURNED_FOR_CORRECTION",
            reason=reason,
            changed_by=request.user,
        )
        
        serializer = self.get_serializer(report, context={"request": request})
        return Response(serializer.data)


class OPDVitalsViewSet(viewsets.ModelViewSet):
    """OPD vitals management"""
    queryset = OPDVitals.objects.select_related("service_visit", "entered_by").all()
    serializer_class = OPDVitalsSerializer
    permission_classes = [IsPerformanceDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(service_visit_id=visit_id)
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            return self.queryset.get(service_visit_id=visit_id)
        except OPDVitals.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("OPD vitals not found for this visit")
    
    def create(self, request):
        """Create or update OPD vitals"""
        visit_id = request.data.get("visit_id") or request.query_params.get("visit_id")
        if not visit_id:
            return Response({"detail": "visit_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service_visit = ServiceVisit.objects.get(id=visit_id)
        except ServiceVisit.DoesNotExist:
            return Response({"detail": "Service visit not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if vitals exist
        vitals, created = OPDVitals.objects.get_or_create(
            service_visit=service_visit,
            defaults={"entered_by": request.user}
        )
        
        if not created:
            # Update vitals
            for field in ["bp_systolic", "bp_diastolic", "pulse", "temperature", 
                          "respiratory_rate", "spo2", "weight", "height", "bmi"]:
                if field in request.data:
                    setattr(vitals, field, request.data[field])
            vitals.save()
        
        # Transition to IN_PROGRESS
        if service_visit.status == "REGISTERED":
            service_visit.status = "IN_PROGRESS"
            service_visit.save()
            StatusAuditLog.objects.create(
                service_visit=service_visit,
                from_status="REGISTERED",
                to_status="IN_PROGRESS",
                changed_by=request.user,
            )
        
        serializer = self.get_serializer(vitals, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OPDConsultViewSet(viewsets.ModelViewSet):
    """OPD consultation management"""
    queryset = OPDConsult.objects.select_related("service_visit", "consultant").all()
    serializer_class = OPDConsultSerializer
    permission_classes = [IsPerformanceDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(service_visit_id=visit_id)
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            return self.queryset.get(service_visit_id=visit_id)
        except OPDConsult.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("OPD consultation not found for this visit")
    
    def create(self, request):
        """Create or update OPD consultation"""
        visit_id = request.data.get("visit_id") or request.query_params.get("visit_id")
        if not visit_id:
            return Response({"detail": "visit_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service_visit = ServiceVisit.objects.get(id=visit_id)
        except ServiceVisit.DoesNotExist:
            return Response({"detail": "Service visit not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if consult exists
        consult, created = OPDConsult.objects.get_or_create(
            service_visit=service_visit,
            defaults={"consultant": request.user}
        )
        
        if not created:
            # Update consult
            for field in ["diagnosis", "notes", "medicines_json", "investigations_json", "advice", "followup"]:
                if field in request.data:
                    setattr(consult, field, request.data[field])
            consult.save()
        
        serializer = self.get_serializer(consult, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"], permission_classes=[IsPerformanceDesk])
    def save_and_print(self, request, pk=None):
        """Save OPD consultation and generate prescription PDF"""
        consult = self.get_object()
        service_visit = consult.service_visit
        
        # Update consult data
        for field in ["diagnosis", "notes", "medicines_json", "investigations_json", "advice", "followup"]:
            if field in request.data:
                setattr(consult, field, request.data[field])
        consult.save()
        
        # Generate prescription PDF
        from .pdf import build_opd_prescription_pdf
        pdf_file = build_opd_prescription_pdf(consult)
        
        # Save PDF
        now = timezone.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs" / "prescriptions" / year / month
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"{service_visit.visit_id}.pdf"
        pdf_path = pdf_dir / pdf_filename
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        
        consult.published_pdf_path = f"pdfs/prescriptions/{year}/{month}/{pdf_filename}"
        consult.save()
        
        # Transition to PUBLISHED
        from_status = service_visit.status
        service_visit.status = "PUBLISHED"
        service_visit.save()
        
        StatusAuditLog.objects.create(
            service_visit=service_visit,
            from_status=from_status,
            to_status="PUBLISHED",
            changed_by=request.user,
        )
        
        serializer = self.get_serializer(consult, context={"request": request})
        return Response(serializer.data)


class PDFViewSet(viewsets.ViewSet):
    """PDF generation and serving"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Get receipt PDF for service visit"""
        try:
            service_visit = ServiceVisit.objects.get(id=pk)
        except ServiceVisit.DoesNotExist:
            return Response({"detail": "Service visit not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get invoice
        try:
            invoice = service_visit.invoice
        except Invoice.DoesNotExist:
            return Response({"detail": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate receipt PDF
        from .pdf import build_service_visit_receipt_pdf
        from apps.studies.models import ReceiptSequence
        
        # Generate receipt number if not exists
        receipt_number = ReceiptSequence.get_next_receipt_number()
        pdf_file = build_service_visit_receipt_pdf(service_visit, invoice)
        
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="receipt_{service_visit.visit_id}.pdf"'
        return response
    
    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request, pk=None):
        """Get USG report PDF"""
        try:
            service_visit = ServiceVisit.objects.get(id=pk)
            report = service_visit.usg_report
        except (ServiceVisit.DoesNotExist, USGReport.DoesNotExist):
            return Response({"detail": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not report.published_pdf_path:
            return Response({"detail": "Report not published"}, status=status.HTTP_404_NOT_FOUND)
        
        pdf_path = Path(settings.MEDIA_ROOT) / report.published_pdf_path
        if not pdf_path.exists():
            return Response({"detail": "PDF file not found"}, status=status.HTTP_404_NOT_FOUND)
        
        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="report_{service_visit.visit_id}.pdf"'
            return response
    
    @action(detail=True, methods=["get"], url_path="prescription")
    def prescription(self, request, pk=None):
        """Get OPD prescription PDF"""
        try:
            service_visit = ServiceVisit.objects.get(id=pk)
            consult = service_visit.opd_consult
        except (ServiceVisit.DoesNotExist, OPDConsult.DoesNotExist):
            return Response({"detail": "Prescription not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not consult.published_pdf_path:
            return Response({"detail": "Prescription not published"}, status=status.HTTP_404_NOT_FOUND)
        
        pdf_path = Path(settings.MEDIA_ROOT) / consult.published_pdf_path
        if not pdf_path.exists():
            return Response({"detail": "PDF file not found"}, status=status.HTTP_404_NOT_FOUND)
        
        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="prescription_{service_visit.visit_id}.pdf"'
            return response
