from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportWorkItemViewSet, ReportProfileViewSet,
    ReportParameterViewSet, ServiceReportProfileViewSet
)

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
router.register(r'parameters', ReportParameterViewSet, basename='reporting-parameters')
router.register(r'service-profiles', ServiceReportProfileViewSet, basename='reporting-service-profiles')

urlpatterns = [
    path('', include(router.urls)),
]
