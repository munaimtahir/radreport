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

@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
