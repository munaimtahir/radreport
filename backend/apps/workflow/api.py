from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db import models
from pathlib import Path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    ServiceCatalog, ServiceVisit, ServiceVisitItem, Invoice, Payment,
    USGReport, OPDVitals, OPDConsult, StatusAuditLog
)
from .serializers import (
    ServiceCatalogSerializer, ServiceVisitSerializer, ServiceVisitItemSerializer, InvoiceSerializer,
    PaymentSerializer, USGReportSerializer, OPDVitalsSerializer,
    OPDConsultSerializer, ServiceVisitCreateSerializer, StatusTransitionSerializer
)
from apps.catalog.models import Service as CatalogService
from apps.catalog.serializers import ServiceSerializer
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


class ServiceCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    DEPRECATED: Use /api/services/ instead.
    This endpoint is kept for backward compatibility only (read-only).
    """
    queryset = CatalogService.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["code", "name", "modality__code"]
    filterset_fields = ["is_active", "category", "modality"]
    ordering_fields = ["name", "code", "price"]


class ServiceVisitViewSet(viewsets.ModelViewSet):
    """Service visit management"""
    queryset = ServiceVisit.objects.select_related("patient", "service", "created_by", "assigned_to").prefetch_related(
        "items__service", "items__service__modality", "status_audit_logs__changed_by"
    ).all()
    serializer_class = ServiceVisitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["visit_id", "patient__name", "patient__patient_reg_no", "patient__mrn", "items__service__name", "items__service_name_snapshot"]
    filterset_fields = ["status"]
    ordering_fields = ["registered_at", "visit_id", "status"]
    
    def get_queryset(self):
        """Filter by workflow and status if provided"""
        queryset = super().get_queryset()
        workflow = self.request.query_params.get("workflow", None)
        status_filter = self.request.query_params.get("status", None)
        
        if workflow:
            if workflow == "USG":
                # Filter by items with department_snapshot == "USG" (set from modality.code)
                # Use department_snapshot (snapshot at time of order) for correct filtering
                queryset = queryset.filter(
                    items__department_snapshot="USG"
                ).distinct()
            elif workflow == "OPD":
                # Filter by items with department_snapshot == "OPD"
                queryset = queryset.filter(
                    items__department_snapshot="OPD"
                ).distinct()
        
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
    queryset = USGReport.objects.select_related(
        "service_visit_item", "service_visit_item__service", "service_visit_item__service_visit",
        "service_visit", "created_by", "updated_by", "verifier"
    ).all()
    serializer_class = USGReportSerializer
    permission_classes = [IsPerformanceOrVerificationDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(
                models.Q(service_visit_id=visit_id) | models.Q(service_visit_item__service_visit_id=visit_id)
            )
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            # Try to find via ServiceVisitItem first
            item = ServiceVisitItem.objects.filter(
                service_visit_id=visit_id,
                service__category="Radiology",
                service__modality__code="USG"
            ).first()
            if item and hasattr(item, 'usg_report'):
                return item.usg_report
            # Fallback to legacy
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
        
        # Find or create USG ServiceVisitItem
        usg_item = service_visit.items.filter(
            service__category="Radiology",
            service__modality__code="USG"
        ).first()
        
        if not usg_item:
            return Response({"detail": "No USG service found in this visit"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if report exists (prefer item-based, fallback to legacy)
        report = None
        if hasattr(usg_item, 'usg_report'):
            report = usg_item.usg_report
            created = False
        else:
            # Try legacy
            report = USGReport.objects.filter(service_visit=service_visit).first()
            if report:
                # Migrate to item-based
                report.service_visit_item = usg_item
                report.save()
                created = False
            else:
                # Create new
                report = USGReport.objects.create(
                    service_visit_item=usg_item,
                    service_visit=service_visit,  # Keep for backward compatibility
                    created_by=request.user,
                    updated_by=request.user,
                )
                created = True
        
        if not created:
            report.updated_by = request.user
            report.report_json = request.data.get("report_json", report.report_json)
            report.save()
        
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
    queryset = OPDVitals.objects.select_related(
        "service_visit_item", "service_visit_item__service", "service_visit_item__service_visit",
        "service_visit", "entered_by"
    ).all()
    serializer_class = OPDVitalsSerializer
    permission_classes = [IsPerformanceDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(
                models.Q(service_visit_id=visit_id) | models.Q(service_visit_item__service_visit_id=visit_id)
            )
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            # Try to find via ServiceVisitItem first
            item = ServiceVisitItem.objects.filter(
                service_visit_id=visit_id,
                service__category="OPD"
            ).first()
            if item and hasattr(item, 'opd_vitals'):
                return item.opd_vitals
            # Fallback to legacy
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
        
        # Find or create OPD ServiceVisitItem
        opd_item = service_visit.items.filter(service__category="OPD").first()
        
        if not opd_item:
            return Response({"detail": "No OPD service found in this visit"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if vitals exist (prefer item-based, fallback to legacy)
        vitals = None
        if hasattr(opd_item, 'opd_vitals'):
            vitals = opd_item.opd_vitals
            created = False
        else:
            # Try legacy
            vitals = OPDVitals.objects.filter(service_visit=service_visit).first()
            if vitals:
                # Migrate to item-based
                vitals.service_visit_item = opd_item
                vitals.save()
                created = False
            else:
                # Create new
                vitals = OPDVitals.objects.create(
                    service_visit_item=opd_item,
                    service_visit=service_visit,  # Keep for backward compatibility
                    entered_by=request.user
                )
                created = True
        
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
    queryset = OPDConsult.objects.select_related(
        "service_visit_item", "service_visit_item__service", "service_visit_item__service_visit",
        "service_visit", "consultant"
    ).all()
    serializer_class = OPDConsultSerializer
    permission_classes = [IsPerformanceDesk]
    
    def get_queryset(self):
        visit_id = self.request.query_params.get("visit_id") or self.kwargs.get("pk")
        if visit_id:
            return self.queryset.filter(
                models.Q(service_visit_id=visit_id) | models.Q(service_visit_item__service_visit_id=visit_id)
            )
        return self.queryset.all()
    
    def get_object(self):
        visit_id = self.kwargs.get("pk")
        try:
            # Try to find via ServiceVisitItem first
            item = ServiceVisitItem.objects.filter(
                service_visit_id=visit_id,
                service__category="OPD"
            ).first()
            if item and hasattr(item, 'opd_consult'):
                return item.opd_consult
            # Fallback to legacy
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
        
        # Find or create OPD ServiceVisitItem
        opd_item = service_visit.items.filter(service__category="OPD").first()
        
        if not opd_item:
            return Response({"detail": "No OPD service found in this visit"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if consult exists (prefer item-based, fallback to legacy)
        consult = None
        if hasattr(opd_item, 'opd_consult'):
            consult = opd_item.opd_consult
            created = False
        else:
            # Try legacy
            consult = OPDConsult.objects.filter(service_visit=service_visit).first()
            if consult:
                # Migrate to item-based
                consult.service_visit_item = opd_item
                consult.save()
                created = False
            else:
                # Create new
                consult = OPDConsult.objects.create(
                    service_visit_item=opd_item,
                    service_visit=service_visit,  # Keep for backward compatibility
                    consultant=request.user
                )
                created = True
        
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
        
        # Generate receipt number if not exists (idempotent - generated on invoice creation or print)
        # This ensures receipt number exists even if paid=0
        if not invoice.receipt_number:
            from apps.studies.models import ReceiptSequence
            with transaction.atomic():
                # Double-check in transaction to avoid race condition
                invoice.refresh_from_db()
                if not invoice.receipt_number:
                    invoice.receipt_number = ReceiptSequence.get_next_receipt_number()
                    invoice.save()
        
        # Generate receipt PDF
        from .pdf import build_service_visit_receipt_pdf
        pdf_file = build_service_visit_receipt_pdf(service_visit, invoice)
        
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="receipt_{invoice.receipt_number or service_visit.visit_id}.pdf"'
        return response
    
    @action(detail=True, methods=["get"], url_path="report")
    def report(self, request, pk=None):
        """Get USG report PDF"""
        try:
            service_visit = ServiceVisit.objects.get(id=pk)
            # Try to find USG report via ServiceVisitItem first, then fallback to legacy
            report = None
            for item in service_visit.items.filter(service__category="Radiology", service__modality__code="USG"):
                if hasattr(item, 'usg_report'):
                    report = item.usg_report
                    break
            if not report:
                # Legacy: try direct relationship
                try:
                    report = service_visit.usg_reports.first()
                except:
                    pass
        except (ServiceVisit.DoesNotExist, USGReport.DoesNotExist):
            return Response({"detail": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not report:
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
            # Try to find OPD consult via ServiceVisitItem first, then fallback to legacy
            consult = None
            for item in service_visit.items.filter(service__category="OPD"):
                if hasattr(item, 'opd_consult'):
                    consult = item.opd_consult
                    break
            if not consult:
                # Legacy: try direct relationship
                try:
                    consult = service_visit.opd_consults.first()
                except:
                    pass
        except (ServiceVisit.DoesNotExist, OPDConsult.DoesNotExist):
            return Response({"detail": "Prescription not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not consult:
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
