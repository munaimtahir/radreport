from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    ReportBlockLibraryViewSet,
    ReportTemplateV2ViewSet,
    ServiceReportTemplateV2ViewSet,
    ReportWorkItemViewSet,
)

router = DefaultRouter()
router.register(r"workitems", ReportWorkItemViewSet, basename="reporting-workitems")
router.register(r"templates-v2", ReportTemplateV2ViewSet, basename="reporting-templates-v2")
router.register(r"service-templates-v2", ServiceReportTemplateV2ViewSet, basename="reporting-service-templates-v2")
router.register(r"block-library", ReportBlockLibraryViewSet, basename="reporting-block-library")

urlpatterns = [
    path("", include(router.urls)),
]
