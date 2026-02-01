from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from apps.reporting.services.baseline_packs import (
    list_packs,
    build_pack_zip,
    seed_pack,
    verify_pack,
)
from apps.reporting.utils import parse_bool


class BaselinePackViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def list(self, request):
        packs = list_packs()
        data = [
            {
                "slug": p.slug,
                "profile_code": p.profile_code,
                "profile_name": p.profile_name,
                "modality": p.modality,
                "version": p.version,
            }
            for p in packs
        ]
        return Response(data)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        try:
            zip_bytes = build_pack_zip(pk)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{pk}.zip"'
        return response

    @action(detail=True, methods=["post"], url_path="seed")
    def seed(self, request, pk=None):
        dry_run = parse_bool(request.query_params.get("dry_run", "true"))
        try:
            result = seed_pack(pk, request.user, dry_run=dry_run)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        status_code = status.HTTP_200_OK if not result.get("errors") else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        try:
            result = verify_pack(pk)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        status_code = status.HTTP_200_OK if result.get("status") == "pass" else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

