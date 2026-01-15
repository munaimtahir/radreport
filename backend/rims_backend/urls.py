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
from apps.templates.api import TemplateViewSet, TemplateVersionViewSet
from apps.studies.api import StudyViewSet, VisitViewSet, ReceiptSettingsViewSet
from apps.reporting.api import ReportViewSet
from apps.audit.api import AuditLogViewSet
from apps.workflow.api import (
    ServiceCatalogViewSet, ServiceVisitViewSet, ServiceVisitItemViewSet,
    USGReportViewSet, OPDVitalsViewSet, OPDConsultViewSet, PDFViewSet
)
from apps.workflow.models import ServiceVisit, Invoice
from apps.workflow.pdf import build_service_visit_receipt_pdf
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
router.register(r"studies", StudyViewSet, basename="studies")
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"reports", ReportViewSet, basename="reports")
router.register(r"audit", AuditLogViewSet, basename="audit")
router.register(r"receipt-settings", ReceiptSettingsViewSet, basename="receipt-settings")
# Workflow endpoints
router.register(r"workflow/service-catalog", ServiceCatalogViewSet, basename="service-catalog")
router.register(r"workflow/visits", ServiceVisitViewSet, basename="service-visits")
router.register(r"workflow/items", ServiceVisitItemViewSet, basename="service-visit-items")  # PHASE C: Item-centric API
router.register(r"workflow/usg", USGReportViewSet, basename="usg-reports")
router.register(r"workflow/opd/vitals", OPDVitalsViewSet, basename="opd-vitals")
router.register(r"workflow/opd/consult", OPDConsultViewSet, basename="opd-consult")
router.register(r"pdf", PDFViewSet, basename="pdf")

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Health check endpoint for load balancers and uptime monitors."""
    from django.db import connection

    db_status = "ok"
    http_status = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        db_status = f"error: {exc}"
        http_status = 503

    version = os.getenv("GIT_SHA") or os.getenv("COMMIT_SHA")

    return JsonResponse({
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "time": timezone.now().isoformat(),
        "version": version,
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
    
    # Generate receipt PDF
    pdf_file = build_service_visit_receipt_pdf(service_visit, invoice)
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
    path("api/", include(router.urls)),
]

# Serve media files - SECURITY WARNING for production
# This approach serves media files through Django which may have performance
# and security implications. For production deployments, consider:
# 1. Using a CDN or object storage (AWS S3, Google Cloud Storage, etc.)
# 2. Serving directly through your web server (Caddy/Nginx) with proper access controls
# 3. Implementing proper authentication/authorization for sensitive files
# For now, serving directly for simplicity, but review for your security requirements
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
