from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    UsgTemplateViewSet, UsgServiceProfileViewSet,
    UsgStudyViewSet, UsgPublishedSnapshotViewSet
)

router = DefaultRouter()
router.register(r'templates', UsgTemplateViewSet, basename='usg-template')
router.register(r'service-profiles', UsgServiceProfileViewSet, basename='usg-service-profile')
router.register(r'studies', UsgStudyViewSet, basename='usg-study')
router.register(r'snapshots', UsgPublishedSnapshotViewSet, basename='usg-snapshot')

urlpatterns = [
    path('', include(router.urls)),
]
