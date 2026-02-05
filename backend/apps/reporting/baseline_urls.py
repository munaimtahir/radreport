from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reporting.baseline_views import BaselinePackViewSet

router = DefaultRouter()
router.register(r'baseline-packs', BaselinePackViewSet, basename='baseline-packs')

urlpatterns = [
    path('', include(router.urls)),
]
