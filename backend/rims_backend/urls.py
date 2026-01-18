import os

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from apps.patients.api import PatientViewSet
from apps.catalog.api import ModalityViewSet, ServiceViewSet
from apps.templates.api import TemplateViewSet, TemplateVersionViewSet, ReportTemplateViewSet, TemplatePackageViewSet
from apps.studies.api import StudyViewSet, VisitViewSet, ReceiptSettingsViewSet
from apps.reporting.api import ReportViewSet, ReportingViewSet
from apps.audit.api import AuditLogViewSet
from apps.workflow.api import (
    ServiceCatalogViewSet, ServiceVisitViewSet, ServiceVisitItemViewSet,
    USGReportViewSet, OPDVitalsViewSet, OPDConsultViewSet, PDFViewSet,
    PatientWorkflowViewSet,
)
from apps.usg.api import (
    UsgTemplateViewSet, UsgServiceProfileViewSet,
    UsgStudyViewSet, UsgPublishedSnapshotViewSet
)
from apps.consultants.api import ConsultantProfileViewSet, ConsultantSettlementViewSet
from apps.workflow.dashboard_api import (
    dashboard_summary, dashboard_worklist, dashboard_flow
)
from apps.workflow.models import ServiceVisit, Invoice
from apps.workflow.pdf import build_receipt_pdf_from_snapshot
from apps.workflow.receipts import get_receipt_snapshot_data
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r"patients", PatientViewSet, basename="patients")
router.register(r"modalities", ModalityViewSet, basename="modalities")
router.register(r"services", ServiceViewSet, basename="services")
router.register(r"templates", TemplateViewSet, basename="templates")
router.register(r"template-versions", TemplateVersionViewSet, basename="template-versions")
router.register(r"report-templates", ReportTemplateViewSet, basename="report-templates")
router.register(r"template-packages", TemplatePackageViewSet, basename="template-packages")
router.register(r"studies", StudyViewSet, basename="studies")
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"reports", ReportViewSet, basename="reports")
router.register(r"reporting", ReportingViewSet, basename="reporting")
router.register(r"audit", AuditLogViewSet, basename="audit")
router.register(r"receipt-settings", ReceiptSettingsViewSet, basename="receipt-settings")
# Workflow endpoints
router.register(r"workflow/service-catalog", ServiceCatalogViewSet, basename="service-catalog")
router.register(r"workflow/visits", ServiceVisitViewSet, basename="service-visits")
router.register(r"workflow/items", ServiceVisitItemViewSet, basename="service-visit-items")  # PHASE C: Item-centric API
router.register(r"workflow/usg", USGReportViewSet, basename="usg-reports")
router.register(r"workflow/opd/vitals", OPDVitalsViewSet, basename="opd-vitals")
router.register(r"workflow/opd/consult", OPDConsultViewSet, basename="opd-consult")
router.register(r"workflow/patients", PatientWorkflowViewSet, basename="workflow-patients")
router.register(r"pdf", PDFViewSet, basename="pdf")
# USG endpoints
router.register(r"usg/templates", UsgTemplateViewSet, basename="usg-templates")
router.register(r"usg/service-profiles", UsgServiceProfileViewSet, basename="usg-service-profiles")
router.register(r"usg/studies", UsgStudyViewSet, basename="usg-studies")
router.register(r"usg/snapshots", UsgPublishedSnapshotViewSet, basename="usg-snapshots")
router.register(r"consultants", ConsultantProfileViewSet, basename="consultants")
router.register(r"consultant-settlements", ConsultantSettlementViewSet, basename="consultant-settlements")

workflow_visit_receipt = ServiceVisitViewSet.as_view({"get": "receipt_reprint"})
workflow_visit_receipt_pdf = ServiceVisitViewSet.as_view({"get": "receipt_reprint_pdf"})

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """
    Health check endpoint for load balancers and uptime monitors.
    Enhanced for dashboard health card.
    """
    from django.db import connection
    import time

    start_time = time.time()
    db_status = "ok"
    http_status = 200
    checks = {}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["db"] = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"
        checks["db"] = "fail"
        http_status = 503
    
    # Check storage (basic check - media root exists)
    try:
        if os.path.exists(settings.MEDIA_ROOT):
            checks["storage"] = "ok"
        else:
            checks["storage"] = "unknown"
    except:
        checks["storage"] = "unknown"
    
    latency_ms = int((time.time() - start_time) * 1000)
    version = os.getenv("GIT_SHA") or os.getenv("COMMIT_SHA") or "unknown"

    return JsonResponse({
        "status": "ok" if db_status == "ok" else "degraded",
        "server_time": timezone.now().isoformat(),
        "version": version,
        "checks": checks,
        "latency_ms": latency_ms,
    }, status=http_status)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health_auth(request):
    """Authenticated health check for validating auth wiring."""
    user = request.user
    groups = list(user.groups.values_list("name", flat=True))
    return JsonResponse({
        "status": "ok",
        "user": user.username,
        "groups": groups,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_me(request):
    """Return current user identity and group membership for RBAC."""
    user = request.user
    groups = list(user.groups.values_list("name", flat=True))
    return JsonResponse({
        "username": user.username,
        "is_superuser": user.is_superuser,
        "groups": groups,
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def receipt_pdf_alt(request, visit_id):
    """Alternative receipt PDF route: /api/pdf/receipt/{visit_id}/ - for compatibility with frontend"""
    try:
        service_visit = ServiceVisit.objects.get(id=visit_id)
    except ServiceVisit.DoesNotExist:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({"detail": "Service visit not found"}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        invoice = service_visit.invoice
    except Invoice.DoesNotExist:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({"detail": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate receipt number if not exists
    if not invoice.receipt_number:
        from apps.studies.models import ReceiptSequence
        from django.db import transaction
        with transaction.atomic():
            invoice.refresh_from_db()
            if not invoice.receipt_number:
                invoice.receipt_number = ReceiptSequence.get_next_receipt_number()
                invoice.save()
    
    # Generate receipt PDF using snapshot data
    snapshot = get_receipt_snapshot_data(service_visit, invoice)
    pdf_file = build_receipt_pdf_from_snapshot(snapshot)
    response = HttpResponse(pdf_file.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_{invoice.receipt_number or service_visit.visit_id}.pdf"'
    return response

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/health/auth/", health_auth),
    path("api/auth/me/", auth_me),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/pdf/receipt/<uuid:visit_id>/", receipt_pdf_alt, name="receipt-pdf-alt"),  # Alternative route for compatibility
    path("api/visits/<uuid:visit_id>/receipt/", workflow_visit_receipt, name="workflow-visit-receipt"),
    path("api/visits/<uuid:visit_id>/receipt/pdf/", workflow_visit_receipt_pdf, name="workflow-visit-receipt-pdf"),
    # Dashboard endpoints
    path("api/dashboard/summary/", dashboard_summary, name="dashboard-summary"),
    path("api/dashboard/worklist/", dashboard_worklist, name="dashboard-worklist"),
    path("api/dashboard/flow/", dashboard_flow, name="dashboard-flow"),
    path("api/", include(router.urls)),
]

# Serve media files only in DEBUG to avoid Django handling /media in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
