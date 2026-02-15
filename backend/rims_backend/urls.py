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

from apps.audit.api import AuditLogViewSet
from apps.workflow.api import (
    ServiceCatalogViewSet, ServiceVisitViewSet, ServiceVisitItemViewSet,
    OPDVitalsViewSet, OPDConsultViewSet, PDFViewSet,
    PatientWorkflowViewSet,
)
from apps.workflow.user_api import UserViewSet, GroupViewSet, PermissionViewSet
from apps.consultants.api import ConsultantProfileViewSet, ConsultantSettlementViewSet, ConsultantBillingRuleViewSet
from apps.workflow.dashboard_api import (
    dashboard_summary, dashboard_worklist, dashboard_flow
)
from apps.workflow.backup_ops import (
    backup_ops_status, backup_ops_backup_now, backup_ops_restore, backup_ops_sync, backup_ops_export, backup_ops_job_status
)
from apps.backups.api import (
    backups_collection,
    backup_detail,
    backup_upload,
    backup_export,
    backup_import,
    backup_restore,
    backup_cloud_test,
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
router.register(r"audit", AuditLogViewSet, basename="audit")
# Workflow endpoints
router.register(r"workflow/service-catalog", ServiceCatalogViewSet, basename="service-catalog")
router.register(r"workflow/visits", ServiceVisitViewSet, basename="service-visits")
router.register(r"workflow/items", ServiceVisitItemViewSet, basename="service-visit-items")  # PHASE C: Item-centric API
router.register(r"workflow/opd/vitals", OPDVitalsViewSet, basename="opd-vitals")
router.register(r"workflow/opd/consult", OPDConsultViewSet, basename="opd-consult")
router.register(r"workflow/patients", PatientWorkflowViewSet, basename="workflow-patients")
router.register(r"pdf", PDFViewSet, basename="pdf")
# Consultants endpoints
router.register(r"consultants", ConsultantProfileViewSet, basename="consultants")
router.register(r"consultant-billing-rules", ConsultantBillingRuleViewSet, basename="consultant-billing-rules")
router.register(r"consultant-settlements", ConsultantSettlementViewSet, basename="consultant-settlements")
# Auth/user management
router.register(r"auth/users", UserViewSet, basename="users")
router.register(r"auth/groups", GroupViewSet, basename="groups")
router.register(r"auth/permissions", PermissionViewSet, basename="permissions")


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
    
    # Generate receipt number if not exists (idempotent)
    if not invoice.receipt_number:
        from apps.sequences.models import get_next_receipt_number
        from django.db import transaction
        with transaction.atomic():
            invoice.refresh_from_db()
            if not invoice.receipt_number:
                invoice.receipt_number = get_next_receipt_number(increment=True)
                invoice.save()
    
    # Generate receipt PDF using snapshot data
    snapshot = get_receipt_snapshot_data(service_visit, invoice)
    pdf_file = build_receipt_pdf_from_snapshot(snapshot)
    response = HttpResponse(pdf_file.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_{invoice.receipt_number or service_visit.visit_id}.pdf"'
    return response

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", health),
    path("healthz/", health),
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
    path("api/backup-ops/status/", backup_ops_status, name="backup-ops-status"),
    path("api/backup-ops/backup-now/", backup_ops_backup_now, name="backup-ops-backup-now"),
    path("api/backup-ops/restore/", backup_ops_restore, name="backup-ops-restore"),
    path("api/backup-ops/sync/", backup_ops_sync, name="backup-ops-sync"),
    path("api/backup-ops/jobs/<str:job_id>/", backup_ops_job_status, name="backup-ops-job-status"),
    path("api/backup-ops/export/<str:backup_date>/", backup_ops_export, name="backup-ops-export"),
    path("api/backups/", backups_collection, name="backups-collection"),
    path("api/backups/import/", backup_import, name="backups-import"),
    path("api/backups/cloud/test/", backup_cloud_test, name="backups-cloud-test"),
    path("api/backups/<str:backup_id>/", backup_detail, name="backup-detail"),
    path("api/backups/<str:backup_id>/upload/", backup_upload, name="backup-upload"),
    path("api/backups/<str:backup_id>/export/", backup_export, name="backup-export"),
    path("api/backups/<str:backup_id>/restore/", backup_restore, name="backup-restore"),
    # Dashboard endpoints
    path("api/dashboard/summary/", dashboard_summary, name="dashboard-summary"),
    path("api/dashboard/worklist/", dashboard_worklist, name="dashboard-worklist"),
    path("api/dashboard/flow/", dashboard_flow, name="dashboard-flow"),
    path("api/reporting/", include("apps.reporting.urls")),
    path("api/printing/", include("apps.printing.urls")),
    path("api/", include(router.urls)),

]

# Serve media files only in DEBUG to avoid Django handling /media in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
