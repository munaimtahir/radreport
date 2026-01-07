from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny
from apps.patients.api import PatientViewSet
from apps.catalog.api import ModalityViewSet, ServiceViewSet
from apps.templates.api import TemplateViewSet, TemplateVersionViewSet
from apps.studies.api import StudyViewSet, VisitViewSet, ReceiptSettingsViewSet
from apps.reporting.api import ReportViewSet
from apps.audit.api import AuditLogViewSet
from apps.workflow.api import (
    ServiceCatalogViewSet, ServiceVisitViewSet, USGReportViewSet,
    OPDVitalsViewSet, OPDConsultViewSet, PDFViewSet
)
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

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
router.register(r"workflow/usg", USGReportViewSet, basename="usg-reports")
router.register(r"workflow/opd/vitals", OPDVitalsViewSet, basename="opd-vitals")
router.register(r"workflow/opd/consult", OPDConsultViewSet, basename="opd-consult")
router.register(r"pdf", PDFViewSet, basename="pdf")

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Enhanced health check endpoint that verifies app, DB, and storage."""
    from django.db import connection
    from pathlib import Path
    import os
    
    status = {
        "status": "ok",
        "app": "rims_backend",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Check static files directory
    static_root = Path(settings.STATIC_ROOT)
    if static_root.exists() and static_root.is_dir():
        status["checks"]["static_files"] = "ok"
    else:
        status["checks"]["static_files"] = "missing"
        status["status"] = "degraded"
    
    # Check media directory
    media_root = Path(settings.MEDIA_ROOT)
    try:
        if not media_root.exists():
            media_root.mkdir(parents=True, exist_ok=True)
        # Check if writable
        test_file = media_root / ".health_check"
        test_file.touch()
        test_file.unlink()
        status["checks"]["media_storage"] = "ok"
    except Exception as e:
        status["checks"]["media_storage"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    http_status = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=http_status)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
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
