from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportWorkItemViewSet

router = DefaultRouter()
# We map 'workitems' to the viewset. 
# The viewset is setup to use 'pk' as the service_visit_item_id.
# Routes will be:
# GET /workitems/{pk}/schema/
# GET /workitems/{pk}/values/
# POST /workitems/{pk}/save/
# POST /workitems/{pk}/submit/

router.register(r'workitems', ReportWorkItemViewSet, basename='reporting-workitems')

urlpatterns = [
    path('', include(router.urls)),
]
