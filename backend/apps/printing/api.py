"""
Printing config API - merged org + receipt branding.
Endpoints match frontend expectations exactly.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.reporting.models import ReportingOrganizationConfig
from apps.sequences.models import get_next_receipt_number

from .models import ReceiptBrandingConfig


def _get_org_config():
    """Get or create ReportingOrganizationConfig singleton."""
    org = ReportingOrganizationConfig.objects.first()
    if not org:
        org = ReportingOrganizationConfig.objects.create(
            org_name="Organization",
            disclaimer_text="This report is electronically verified.",
        )
    return org


def _get_merged_config():
    """Build merged config dict for frontend."""
    org = _get_org_config()
    receipt = ReceiptBrandingConfig.get_singleton()

    return {
        "org_name": org.org_name or "",
        "address": org.address or "",
        "phone": org.phone or "",
        "disclaimer_text": org.disclaimer_text or "",
        "signatories_json": org.signatories_json or [],
        "report_logo_url": org.logo.url if org.logo else None,
        "receipt_header_text": receipt.receipt_header_text or "",
        "receipt_footer_text": receipt.receipt_footer_text or "",
        "receipt_logo_url": receipt.receipt_logo.url if receipt.receipt_logo else None,
        "receipt_banner_url": receipt.receipt_banner.url if receipt.receipt_banner else None,
        "updated_at": (receipt.updated_at.isoformat() if receipt.updated_at else None)
        or (org.updated_at.isoformat() if org.updated_at else None),
    }


@api_view(["GET", "PATCH"])
def printing_config(request):
    """GET or PATCH /api/printing/config/ - merged org + receipt config."""
    if request.method == "GET":
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        config = _get_merged_config()
        return Response(config)
    # PATCH
    if not request.user or not request.user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"detail": "Admin required"}, status=status.HTTP_403_FORBIDDEN)
    return _printing_config_patch(request)


def _printing_config_patch(request):
    """Update both configs from payload."""
    data = request.data
    if not isinstance(data, dict):
        return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate signatories_json
    sigs = data.get("signatories_json")
    if sigs is not None:
        if not isinstance(sigs, list):
            return Response(
                {"detail": "signatories_json must be a list of {name, designation}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for item in sigs:
            if not isinstance(item, dict) or "name" not in item or "designation" not in item:
                return Response(
                    {"detail": "Each signatory must have name and designation"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    org = _get_org_config()

    org_fields = ["org_name", "address", "phone", "disclaimer_text", "signatories_json"]
    for f in org_fields:
        if f in data:
            setattr(org, f, data[f])
    org.save()

    receipt = ReceiptBrandingConfig.get_singleton()
    receipt_fields = ["receipt_header_text", "receipt_footer_text"]
    for f in receipt_fields:
        if f in data:
            setattr(receipt, f, data[f])
    receipt.save()

    return Response(_get_merged_config())


def _build_absolute_uri(path):
    """Build absolute URL for media files if request available."""
    if path and settings.MEDIA_URL:
        base = getattr(settings, "SITE_URL", "") or ""
        return f"{base.rstrip('/')}{path}"
    return path


@api_view(["POST"])
@permission_classes([IsAdminUser])
def upload_report_logo(request):
    """POST /api/printing/config/upload-report_logo/ - expects report_logo file."""
    f = request.FILES.get("report_logo")
    if not f:
        return Response({"detail": "report_logo file required"}, status=status.HTTP_400_BAD_REQUEST)
    org = _get_org_config()
    org.logo = f
    org.save()
    return Response(_get_merged_config())


@api_view(["POST"])
@permission_classes([IsAdminUser])
def upload_receipt_logo(request):
    """POST /api/printing/config/upload-receipt_logo/ - expects receipt_logo file."""
    f = request.FILES.get("receipt_logo")
    if not f:
        return Response({"detail": "receipt_logo file required"}, status=status.HTTP_400_BAD_REQUEST)
    receipt = ReceiptBrandingConfig.get_singleton()
    receipt.receipt_logo = f
    receipt.save()
    return Response(_get_merged_config())


@api_view(["POST"])
@permission_classes([IsAdminUser])
def upload_receipt_banner(request):
    """POST /api/printing/config/upload-receipt_banner/ - expects receipt_banner file."""
    f = request.FILES.get("receipt_banner")
    if not f:
        return Response({"detail": "receipt_banner file required"}, status=status.HTTP_400_BAD_REQUEST)
    receipt = ReceiptBrandingConfig.get_singleton()
    receipt.receipt_banner = f
    receipt.save()
    return Response(_get_merged_config())


@api_view(["GET"])
@permission_classes([IsAdminUser])
def sequence_next(request):
    """GET /api/printing/sequence/next?type=receipt&dry_run=1 -> { next: YYMM-#### }"""
    seq_type = request.query_params.get("type", "")
    dry_run = request.query_params.get("dry_run", "0") in ("1", "true", "yes")
    if seq_type != "receipt":
        return Response({"detail": "Only type=receipt supported"}, status=status.HTTP_400_BAD_REQUEST)
    next_val = get_next_receipt_number(increment=not dry_run)
    return Response({"next": next_val})
