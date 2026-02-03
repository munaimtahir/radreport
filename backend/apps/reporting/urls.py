from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportWorkItemViewSet, ReportProfileViewSet,
    ReportParameterViewSet, ServiceReportProfileViewSet,
    ReportParameterLibraryItemViewSet,
    ReportTemplateV2ViewSet, ServiceReportTemplateV2ViewSet,
    ReportBlockLibraryViewSet
)
from .governance_views import TemplateGovernanceViewSet, TemplateAuditLogViewSet

router = DefaultRouter()
# We map 'workitems' to the viewset. 
# The viewset is setup to use 'pk' as the service_visit_item_id.
# Routes will be:
# GET /workitems/{pk}/schema/
# GET /workitems/{pk}/values/
# POST /workitems/{pk}/save/
# POST /workitems/{pk}/submit/

router.register(r'workitems', ReportWorkItemViewSet, basename='reporting-workitems')
router.register(r'profiles', ReportProfileViewSet, basename='reporting-profiles')
router.register(r'templates-v2', ReportTemplateV2ViewSet, basename='reporting-templates-v2')
router.register(r'parameters', ReportParameterViewSet, basename='reporting-parameters')
router.register(r'service-profiles', ServiceReportProfileViewSet, basename='reporting-service-profiles')
router.register(r'service-templates-v2', ServiceReportTemplateV2ViewSet, basename='reporting-service-templates-v2')
router.register(r'parameter-library', ReportParameterLibraryItemViewSet, basename='reporting-parameter-library')
router.register(r'block-library', ReportBlockLibraryViewSet, basename='reporting-block-library')

# Governance endpoints
router.register(r'governance', TemplateGovernanceViewSet, basename='template-governance')
router.register(r'audit-logs', TemplateAuditLogViewSet, basename='template-audit-logs')

urlpatterns = [
    path('', include(router.urls)),
]
