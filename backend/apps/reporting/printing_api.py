from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PrintingConfig, PrintingSequence
from .serializers import PrintingConfigSerializer


class PrintingConfigViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        cfg = PrintingConfig.get()
        data = PrintingConfigSerializer(cfg, context={"request": request}).data
        return Response(data)

    def partial_update(self, request, pk=None):
        cfg = PrintingConfig.get()
        serializer = PrintingConfigSerializer(cfg, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)

    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    def create(self, request):
        return self.partial_update(request, pk=None)

    @action(detail=False, methods=["post"], url_path="upload-report_logo")
    def upload_report_logo(self, request):
        if "report_logo" not in request.FILES:
            return Response({"detail": "report_logo file is required"}, status=status.HTTP_400_BAD_REQUEST)
        cfg = PrintingConfig.get()
        cfg.report_logo = request.FILES["report_logo"]
        cfg.updated_by = request.user
        cfg.save()
        return Response(PrintingConfigSerializer(cfg, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="upload-receipt_logo")
    def upload_receipt_logo(self, request):
        if "receipt_logo" not in request.FILES:
            return Response({"detail": "receipt_logo file is required"}, status=status.HTTP_400_BAD_REQUEST)
        cfg = PrintingConfig.get()
        cfg.receipt_logo = request.FILES["receipt_logo"]
        cfg.updated_by = request.user
        cfg.save()
        return Response(PrintingConfigSerializer(cfg, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="upload-receipt_banner")
    def upload_receipt_banner(self, request):
        if "receipt_banner" not in request.FILES:
            return Response({"detail": "receipt_banner file is required"}, status=status.HTTP_400_BAD_REQUEST)
        cfg = PrintingConfig.get()
        cfg.receipt_banner = request.FILES["receipt_banner"]
        cfg.updated_by = request.user
        cfg.save()
        return Response(PrintingConfigSerializer(cfg, context={"request": request}).data)


class PrintingSequenceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        seq_type = request.query_params.get("type", "receipt")
        dry_run = request.query_params.get("dry_run", "0") in ("1", "true", "True")
        if dry_run:
            next_num = self.preview_next(seq_type)
            return Response({"next": next_num})
        next_num = PrintingSequence.next_number(seq_type)
        return Response({"next": next_num})

    def preview_next(self, seq_type):
        from django.utils import timezone
        now = timezone.now()
        yymm = now.strftime("%y%m")
        last = PrintingSequence.objects.filter(seq_type=seq_type, yymm=yymm).first()
        next_num = (last.last_number + 1) if last else 1
        return f"{yymm}-{str(next_num).zfill(4)}"
