from django.urls import path
from . import api

urlpatterns = [
    path("config/", api.printing_config),
    path("config/upload-report_logo/", api.upload_report_logo),
    path("config/upload-receipt_logo/", api.upload_receipt_logo),
    path("config/upload-receipt_banner/", api.upload_receipt_banner),
    path("sequence/next/", api.sequence_next),
]
