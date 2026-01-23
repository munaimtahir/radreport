import logging
from decimal import Decimal
from datetime import datetime, time

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db import models
from django.db.models import Exists, OuterRef, Q, Subquery
from pathlib import Path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    ServiceVisit, ServiceVisitItem, Invoice, Payment,
    OPDVitals, OPDConsult, StatusAuditLog
)
from .serializers import (
    ServiceVisitSerializer, ServiceVisitItemSerializer, InvoiceSerializer,
    PaymentSerializer, OPDVitalsSerializer,
    OPDConsultSerializer, ServiceVisitCreateSerializer, StatusTransitionSerializer
)

from .pdf import build_receipt_pdf_from_snapshot
from apps.catalog.models import Service as CatalogService
from apps.catalog.serializers import ServiceSerializer
from .permissions import (
    IsRegistrationDesk, IsPerformanceDesk, IsVerificationDesk,
    IsRegistrationOrPerformanceDesk, IsPerformanceOrVerificationDesk, IsAnyDesk,
    IsUSGOperator, IsVerifier, IsOPDOperator, IsDoctor, IsReception
)
from .transitions import transition_item_status, get_allowed_transitions
from django.core.exceptions import ValidationError, SuspiciousFileOperation
from rest_framework.exceptions import PermissionDenied, NotFound
from apps.patients.models import Patient
from .receipts import get_receipt_snapshot_data

logger = logging.getLogger(__name__)


WORKFLOW_STATUS_CHOICES = (
    "registered",
    "services_added",
    "paid",
    "sample_collected",
    "report_pending",
    "report_ready",
    "report_published",
)


def _parse_date_param(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(f"Invalid date format: {value}. Expected YYYY-MM-DD.") from exc


def _date_range_from_params(request):
    date_from = _parse_date_param(request.query_params.get("date_from"))
    date_to = _parse_date_param(request.query_params.get("date_to"))
    tz = timezone.get_current_timezone()
    start = None
    end = None
    if date_from:
        start = timezone.make_aware(datetime.combine(date_from, time.min), tz)
    if date_to:
        end = timezone.make_aware(datetime.combine(date_to, time.max), tz)
    return start, end


def _is_numeric_search(value: str) -> bool:
    if not value:
        return False
    digits = "".join(ch for ch in value if ch.isdigit())
    return bool(digits)


def _compute_workflow_status(service_visit):
    """
    Compute workflow status for display.
    """
    items = list(service_visit.items.all())
    if not items:
        return "registered"

    total_paid = sum((payment.amount_paid for payment in service_visit.payments.all()), Decimal("0"))
    if total_paid <= 0:
        return "services_added"

    # Check item statuses
    statuses = [item.status for item in items]
    
    if all(s == "PUBLISHED" for s in statuses):
        return "report_published"
    
    if any(s == "PUBLISHED" for s in statuses):
        # Mixed status, but at least one published
        return "report_published" # Or report_ready?

    if any(s == "FINALIZED" for s in statuses):
         return "report_ready"

    if any(s in ("PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION") for s in statuses):
        return "report_pending"
        
    if any(s == "IN_PROGRESS" for s in statuses):
        return "sample_collected"

    return "paid"



def _build_receipt_info(service_visit):
    invoice = getattr(service_visit, "invoice", None)
    if not invoice or not invoice.receipt_number:
        return {
            "available": False,
            "receipt_id": None,
            "pdf_url": None,
        }
    return {
        "available": True,
        "receipt_id": str(invoice.id),
        "pdf_url": f"/api/workflow/visits/{service_visit.id}/receipt/pdf/",
    }


def _build_reports_info(service_visit):
    return {
        "available": False,
        "items": [],
    }



def _serialize_receipt_snapshot(snapshot, service_visit):
    total_amount = snapshot.subtotal - snapshot.discount
    return {
        "visit_id": str(service_visit.id),
        "visit_code": service_visit.visit_id,
        "receipt_number": snapshot.receipt_number,
        "issued_at": snapshot.issued_at.isoformat(),
        "patient": {
            "name": snapshot.patient_name,
            "mrn": snapshot.patient_mrn,
            "reg_no": snapshot.patient_reg_no,
            "age": snapshot.patient_age,
            "gender": snapshot.patient_gender,
            "phone": snapshot.patient_phone,
        },
        "items": snapshot.items_json,
        "subtotal": str(snapshot.subtotal),
        "discount": str(snapshot.discount),
        "total_amount": str(total_amount),
        "total_paid": str(snapshot.total_paid),
        "payment_method": snapshot.payment_method,
        "cashier": snapshot.cashier_name,
        "pdf_url": f"/api/workflow/visits/{service_visit.id}/receipt/pdf/",
    }

def _resolve_media_path(relative_path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    candidate = (media_root / relative_path).resolve()
    if not str(candidate).startswith(str(media_root)):
        raise SuspiciousFileOperation(f"Blocked path traversal: {relative_path}")
    return candidate
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
            return f"{yymm}-0001"


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
    permission_classes = [IsAnyDesk]
    filter_backends = [SearchFilter, OrderingFilter]  # Removed DjangoFilterBackend - status filtering handled in get_queryset
    search_fields = ["visit_id", "patient__name", "patient__patient_reg_no", "patient__mrn", "items__service__name", "items__service_name_snapshot"]
    # Removed filterset_fields - status filtering with comma-separated values handled in get_queryset
    ordering_fields = ["registered_at", "visit_id", "status"]
    
    def get_queryset(self):
        """Filter by workflow and status if provided"""
        queryset = super().get_queryset()
        workflow = self.request.query_params.get("workflow", None)
        
        # Support both repeated query params and comma-separated values for status
        status_list = self.request.query_params.getlist("status")
        status_filter = self.request.query_params.get("status", None)
        
        if workflow:
            if workflow == "USG":
                # Filter by items with department_snapshot == "USG" (set from modality.code)
                # Use department_snapshot (snapshot at time of order) for correct filtering
                queryset = queryset.filter(
                    items__department_snapshot="USG"
                ).distinct()
            elif workflow == "OPD":
                if not settings.OPD_ENABLED:
                    raise NotFound("OPD disabled")
                # Filter by items with department_snapshot == "OPD"
                queryset = queryset.filter(
                    items__department_snapshot="OPD"
                ).distinct()
        
        # Handle status filtering: prefer repeated params, fallback to comma-separated
        if status_list:
            # Multiple status values from repeated query params (e.g., ?status=REGISTERED&status=RETURNED_FOR_CORRECTION)
            queryset = queryset.filter(status__in=status_list)
        elif status_filter:
            # Support comma-separated values for backward compatibility (e.g., ?status=REGISTERED,RETURNED_FOR_CORRECTION)
            if "," in status_filter:
                statuses = [s.strip() for s in status_filter.split(",")]
                queryset = queryset.filter(status__in=statuses)
            else:
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

    @action(detail=True, methods=["get"], url_path="receipt", permission_classes=[IsAnyDesk])
    def receipt_reprint(self, request, pk=None):
        """Read-only receipt payload for reprinting."""
        service_visit = self.get_object()
        try:
            invoice = service_visit.invoice
        except Invoice.DoesNotExist:
            return Response({"detail": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        if not invoice.receipt_number:
            return Response({"detail": "Receipt not finalized"}, status=status.HTTP_404_NOT_FOUND)

        snapshot = get_receipt_snapshot_data(service_visit, invoice)
        return Response(_serialize_receipt_snapshot(snapshot, service_visit))

    @action(detail=True, methods=["get"], url_path="receipt/pdf", permission_classes=[IsAnyDesk])
    def receipt_reprint_pdf(self, request, pk=None):
        """Read-only receipt PDF for reprinting."""
        service_visit = self.get_object()
        try:
            invoice = service_visit.invoice
        except Invoice.DoesNotExist:
            return Response({"detail": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)

        if not invoice.receipt_number:
            return Response({"detail": "Receipt not finalized"}, status=status.HTTP_404_NOT_FOUND)

        snapshot = get_receipt_snapshot_data(service_visit, invoice)
        pdf_file = build_receipt_pdf_from_snapshot(snapshot)
        filename = f"receipt_{service_visit.visit_id}.pdf"
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class ServiceVisitItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    PHASE C: Item-centric API for ServiceVisitItems.
    This is the primary interface for worklists and item operations.
    """
    queryset = ServiceVisitItem.objects.select_related(
        "service_visit", "service_visit__patient", "service", "service__modality"
    ).prefetch_related(
        "status_audit_logs__changed_by"
    ).all()
    serializer_class = ServiceVisitItemSerializer
    permission_classes = [IsAnyDesk]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["service_name_snapshot", "service_visit__visit_id", "service_visit__patient__name", "service_visit__patient__mrn"]
    filterset_fields = ["status", "department_snapshot"]
    ordering_fields = ["created_at", "updated_at", "status"]
    
    def get_queryset(self):
        """PHASE C: Item-centric worklist filtering"""
        queryset = super().get_queryset()
        
        # Filter by department (workflow)
        department = self.request.query_params.get("department", None)
        if department:
            if department == "OPD" and not settings.OPD_ENABLED:
                raise NotFound("OPD disabled")
            queryset = queryset.filter(department_snapshot=department)
        
        # Filter by status
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            # Support multiple statuses (comma-separated)
            if "," in status_filter:
                statuses = [s.strip() for s in status_filter.split(",")]
                queryset = queryset.filter(status__in=statuses)
            else:
                queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=["post"], permission_classes=[IsAnyDesk])
    def transition_status(self, request, pk=None):
        """
        PHASE C: Transition item status using transition service.
        This is the ONLY way to change item status - enforces valid transitions and permissions.
        """
        item = self.get_object()
        to_status = request.data.get("to_status")
        reason = request.data.get("reason", "")
        
        if not to_status:
            return Response(
                {"detail": "to_status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transition_item_status(item, to_status, request.user, reason)
            item.refresh_from_db()
            serializer = self.get_serializer(item, context={"request": request})
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionDenied as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=False, methods=["get"], permission_classes=[IsAnyDesk])
    def worklist(self, request):
        """
        PHASE C: Item-centric worklist endpoint.
        Returns items filtered by department and status.
        
        Query params:
        - department: USG or OPD
        - status: comma-separated list of statuses (e.g., "REGISTERED,IN_PROGRESS")
        """
        queryset = self.get_queryset()
        
        # Serialize with visit and patient info
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class OPDVitalsViewSet(viewsets.ModelViewSet):
    """OPD vitals management"""
    queryset = OPDVitals.objects.select_related(
        "service_visit_item", "service_visit_item__service", "service_visit_item__service_visit",
        "service_visit", "entered_by"
    ).all()
    serializer_class = OPDVitalsSerializer
    permission_classes = [IsPerformanceDesk]

    def initial(self, request, *args, **kwargs):
        if not settings.OPD_ENABLED:
            raise NotFound("OPD disabled")
        return super().initial(request, *args, **kwargs)
    
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

    def initial(self, request, *args, **kwargs):
        if not settings.OPD_ENABLED:
            raise NotFound("OPD disabled")
        return super().initial(request, *args, **kwargs)
    
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


class PatientWorkflowViewSet(viewsets.ViewSet):
    """Patient workflow viewer APIs (list and timeline)."""
    permission_classes = [IsAnyDesk]

    def _get_pagination(self, request):
        paginator = PageNumberPagination()
        page_size = request.query_params.get("page_size", None)
        if page_size:
            try:
                paginator.page_size = max(1, min(int(page_size), 100))
            except ValueError:
                paginator.page_size = 20
        else:
            paginator.page_size = 20
        return paginator

    def _base_patient_queryset(self, request):
        search = (request.query_params.get("search") or "").strip()
        start, end = _date_range_from_params(request)

        latest_visit = ServiceVisit.objects.filter(patient=OuterRef("pk"))
        if start:
            latest_visit = latest_visit.filter(registered_at__gte=start)
        if end:
            latest_visit = latest_visit.filter(registered_at__lte=end)

        patient_queryset = Patient.objects.all()

        if search:
            patient_filter = (
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(mrn__icontains=search)
                | Q(patient_reg_no__icontains=search)
            )
            if _is_numeric_search(search):
                digits = "".join(ch for ch in search if ch.isdigit())
                patient_filter = patient_filter | Q(phone__icontains=digits)

            visit_search = ServiceVisit.objects.filter(
                patient=OuterRef("pk")
            ).filter(
                Q(visit_id__icontains=search)
                | Q(invoice__receipt_number__icontains=search)
            )
            patient_queryset = patient_queryset.filter(patient_filter | Exists(visit_search))

        patient_queryset = patient_queryset.annotate(
            latest_visit_id=Subquery(latest_visit.order_by("-registered_at").values("id")[:1]),
            last_visit_at=Subquery(latest_visit.order_by("-registered_at").values("registered_at")[:1]),
        ).filter(latest_visit_id__isnull=False)

        return patient_queryset.order_by("-last_visit_at")

    def list(self, request):
        status_filter = (request.query_params.get("status") or "").strip().lower()
        start, end = _date_range_from_params(request)

        if status_filter and status_filter not in WORKFLOW_STATUS_CHOICES:
            return Response(
                {"detail": f"Invalid status filter '{status_filter}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient_queryset = self._base_patient_queryset(request)

        paginator = self._get_pagination(request)

        if status_filter:
            patient_list = list(patient_queryset)
            latest_visit_ids = [p.latest_visit_id for p in patient_list if p.latest_visit_id]
            visits = ServiceVisit.objects.filter(
                id__in=latest_visit_ids
            ).select_related(
                "patient", "invoice"
            ).prefetch_related(
                "payments"
            )
            visit_map = {visit.id: visit for visit in visits}

            filtered_patients = []
            for patient in patient_list:
                visit = visit_map.get(patient.latest_visit_id)
                if not visit:
                    continue
                workflow_status = _compute_workflow_status(visit)
                if workflow_status == status_filter:
                    filtered_patients.append(patient)

            page = paginator.paginate_queryset(filtered_patients, request, view=self)
        else:
            page = paginator.paginate_queryset(patient_queryset, request, view=self)

        latest_visit_ids = [p.latest_visit_id for p in page if p.latest_visit_id]
        visits = ServiceVisit.objects.filter(
            id__in=latest_visit_ids
        ).select_related(
            "patient", "invoice"
        ).prefetch_related(
            "payments"
        )
        visit_map = {visit.id: visit for visit in visits}

        results = []
        for patient in page:
            visit = visit_map.get(patient.latest_visit_id)
            if not visit:
                continue
            workflow_status = _compute_workflow_status(visit)
            results.append(
                {
                    "patient_id": str(patient.id),
                    "mrn": patient.mrn,
                    "reg_no": patient.patient_reg_no,
                    "name": patient.name,
                    "age": patient.age,
                    "sex": patient.gender,
                    "phone": patient.phone,
                    "last_visit_at": patient.last_visit_at.isoformat() if patient.last_visit_at else None,
                    "latest_visit_id": str(visit.id),
                    "workflow_status": workflow_status,
                    "receipt": _build_receipt_info(visit),
                    "reports": _build_reports_info(visit),
                }
            )

        response = paginator.get_paginated_response(results)
        response.data["date_from"] = start.isoformat() if start else None
        response.data["date_to"] = end.isoformat() if end else None
        return response

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        start, end = _date_range_from_params(request)

        try:
            patient = Patient.objects.get(id=pk)
        except Patient.DoesNotExist:
            return Response({"detail": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        visits = ServiceVisit.objects.filter(patient=patient)
        if start:
            visits = visits.filter(registered_at__gte=start)
        if end:
            visits = visits.filter(registered_at__lte=end)
        visits = visits.select_related("patient", "invoice").prefetch_related(
            "payments"
        ).order_by("-registered_at")

        visit_results = []
        for visit in visits:
            visit_results.append(
                {
                    "visit_id": str(visit.id),
                    "visit_code": visit.visit_id,
                    "registered_at": visit.registered_at.isoformat(),
                    "workflow_status": _compute_workflow_status(visit),
                    "receipt": _build_receipt_info(visit),
                    "reports": _build_reports_info(visit),
                }
            )

        return Response(
            {
                "patient": {
                    "id": str(patient.id),
                    "mrn": patient.mrn,
                    "reg_no": patient.patient_reg_no,
                    "name": patient.name,
                    "age": patient.age,
                    "sex": patient.gender,
                    "phone": patient.phone,
                },
                "date_from": start.isoformat() if start else None,
                "date_to": end.isoformat() if end else None,
                "visits": visit_results,
            }
        )


class PDFViewSet(viewsets.ViewSet):
    """PDF generation and serving"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        """Get receipt PDF for service visit - route: /api/pdf/{pk}/receipt/"""
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
        
        # Generate receipt PDF using snapshot data
        snapshot = get_receipt_snapshot_data(service_visit, invoice)
        pdf_file = build_receipt_pdf_from_snapshot(snapshot)
        
        # Create filename based on visit ID for receipts.
        filename = f"receipt_{service_visit.visit_id}.pdf"
        
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
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

        expected_path = report.published_pdf_path
        try:
            pdf_path = _resolve_media_path(expected_path)
        except SuspiciousFileOperation:
            logger.warning(
                "workflow_pdf_invalid_path",
                extra={
                    "event": "workflow_pdf_invalid_path",
                    "service_visit_id": str(service_visit.id),
                    "report_id": str(report.id),
                    "expected_path": expected_path,
                },
            )
            return Response(
                {"detail": f"PDF path invalid for report {report.id} at {expected_path}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not pdf_path.exists():
            logger.warning(
                "workflow_pdf_missing",
                extra={
                    "event": "workflow_pdf_missing",
                    "service_visit_id": str(service_visit.id),
                    "report_id": str(report.id),
                    "expected_path": expected_path,
                },
            )
            return Response(
                {"detail": f"PDF file not found for report {report.id} at {expected_path}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="report_{service_visit.visit_id}.pdf"'
            return response
    
    @action(detail=True, methods=["get"], url_path="prescription")
    def prescription(self, request, pk=None):
        """Get OPD prescription PDF"""
        if not settings.OPD_ENABLED:
            return Response({"detail": "OPD disabled"}, status=status.HTTP_404_NOT_FOUND)
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

        expected_path = consult.published_pdf_path
        try:
            pdf_path = _resolve_media_path(expected_path)
        except SuspiciousFileOperation:
            logger.warning(
                "workflow_pdf_invalid_path",
                extra={
                    "event": "workflow_pdf_invalid_path",
                    "service_visit_id": str(service_visit.id),
                    "consult_id": str(consult.id),
                    "expected_path": expected_path,
                },
            )
            return Response(
                {"detail": f"PDF path invalid for consult {consult.id} at {expected_path}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not pdf_path.exists():
            logger.warning(
                "workflow_pdf_missing",
                extra={
                    "event": "workflow_pdf_missing",
                    "service_visit_id": str(service_visit.id),
                    "consult_id": str(consult.id),
                    "expected_path": expected_path,
                },
            )
            return Response(
                {"detail": f"PDF file not found for consult {consult.id} at {expected_path}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="prescription_{service_visit.visit_id}.pdf"'
            return response
