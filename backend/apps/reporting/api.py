from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import Report, ReportTemplateReport
from .serializers import ReportSerializer, ReportTemplateReportSerializer
from .pdf import build_basic_pdf
from apps.templates.models import TemplateVersion, ReportTemplate, ServiceReportTemplate
from apps.templates.serializers import ReportTemplateDetailSerializer
from apps.studies.models import Study
from apps.audit.models import AuditLog
from apps.workflow.models import ServiceVisitItem
from apps.workflow.permissions import IsAnyDesk
from apps.workflow.transitions import transition_item_status
from django.core.exceptions import ValidationError, PermissionDenied
import logging

logger = logging.getLogger(__name__)

class ReportViewSet(viewsets.ModelViewSet):
    """
    LEGACY: Report model is deprecated. Use USGReport/OPDConsult workflow instead.
    Write operations (POST/PUT/PATCH/DELETE) are blocked for non-admin users.
    Read operations are allowed for backward compatibility.
    """
    queryset = Report.objects.select_related("study","study__patient","study__service","template_version").all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["study__accession", "study__patient__name", "study__service__name"]
    filterset_fields = ["status", "study__service__modality__code"]
    
    def get_permissions(self):
        """Block write operations for non-admin users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'create_for_study', 'save_draft', 'finalize']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["post"])
    def create_for_study(self, request):
        study_id = request.data.get("study_id")
        template_version_id = request.data.get("template_version_id")

        if not study_id or not template_version_id:
            return Response({"detail":"study_id and template_version_id are required"}, status=400)

        study = Study.objects.get(id=study_id)
        tv = TemplateVersion.objects.get(id=template_version_id)

        report, created = Report.objects.get_or_create(study=study, defaults={"template_version": tv})
        if not created and report.template_version_id != tv.id and report.status == "draft":
            report.template_version = tv
            report.save()

        AuditLog.objects.create(actor=request.user, action="report.create_for_study", entity_type="Report", entity_id=str(report.id),
                                meta={"study_id": str(study.id), "template_version_id": str(tv.id)})

        return Response(ReportSerializer(report).data, status=201 if created else 200)

    @action(detail=True, methods=["post"])
    def save_draft(self, request, pk=None):
        report = self.get_object()
        if report.status != "draft":
            return Response({"detail":"Cannot edit a finalized report"}, status=400)

        report.values = request.data.get("values", report.values)
        report.narrative = request.data.get("narrative", report.narrative)
        report.impression = request.data.get("impression", report.impression)
        report.save()

        AuditLog.objects.create(actor=request.user, action="report.save_draft", entity_type="Report", entity_id=str(report.id))
        return Response(ReportSerializer(report).data)

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        report = self.get_object()
        if report.status == "final":
            return Response({"detail":"Already finalized"}, status=400)

        report.status = "final"
        report.finalized_by = request.user
        report.finalized_at = timezone.now()

        # Build and store PDF
        pdf_file = build_basic_pdf(report)
        report.pdf_file.save(pdf_file.name, pdf_file, save=False)
        report.save()

        # Update study status
        s = report.study
        s.status = "final"
        s.save(update_fields=["status"])

        AuditLog.objects.create(actor=request.user, action="report.finalize", entity_type="Report", entity_id=str(report.id),
                                meta={"pdf": report.pdf_file.name})
        return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        report = self.get_object()
        if not report.pdf_file:
            return Response({"detail": "PDF not available"}, status=status.HTTP_404_NOT_FOUND)
        try:
            return FileResponse(report.pdf_file.open(), content_type="application/pdf", filename=f"{report.study.accession}.pdf")
        except (ValueError, IOError):
            raise Http404("PDF file not found")


class ReportingViewSet(viewsets.ViewSet):
    permission_classes = [IsAnyDesk]

    def _get_default_template(self, item):
        link = ServiceReportTemplate.objects.filter(
            service=item.service, is_active=True
        ).select_related("template").order_by("-is_default", "-created_at").first()
        return link.template if link else None

    def _validate_template_values(self, template, values, enforce_required):
        errors = {}
        fields = template.fields.filter(is_active=True).prefetch_related("options")
        for field in fields:
            if field.field_type in ["heading", "separator"]:
                continue
            value = values.get(field.key)
            if enforce_required and field.is_required:
                if field.field_type == "checkbox":
                    if value is not True:
                        errors[field.key] = "Required checkbox must be checked."
                elif value is None or value == "" or value == []:
                    errors[field.key] = "This field is required."
            if value is None:
                continue
            if field.field_type in ["dropdown", "radio"]:
                allowed = {opt.value for opt in field.options.filter(is_active=True)}
                if value not in allowed:
                    errors[field.key] = "Invalid option."
        return errors

    @action(detail=True, methods=["get"], url_path="template")
    def template(self, request, pk=None):
        item = get_object_or_404(ServiceVisitItem, pk=pk)
        template = self._get_default_template(item)
        report = ReportTemplateReport.objects.filter(service_visit_item=item).first()
        return Response({
            "template": ReportTemplateDetailSerializer(template).data if template else None,
            "report": ReportTemplateReportSerializer(report).data if report else None,
        })

    @action(detail=True, methods=["post"], url_path="save-template-report")
    def save_template_report(self, request, pk=None):
        item = get_object_or_404(ServiceVisitItem, pk=pk)
        template_id = request.data.get("template_id")
        values = request.data.get("values") or {}
        narrative_text = request.data.get("narrative_text", "")
        submit = bool(request.data.get("submit"))

        if not isinstance(values, dict):
            return Response({"detail": "values must be an object"}, status=status.HTTP_400_BAD_REQUEST)

        template = None
        if template_id:
            template = get_object_or_404(ReportTemplate, pk=template_id)
        else:
            template = self._get_default_template(item)

        if not template or not template.is_active:
            return Response({"detail": "No active template available for this service"}, status=status.HTTP_400_BAD_REQUEST)

        errors = self._validate_template_values(template, values, submit)
        if errors:
            return Response({"detail": "Validation failed", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        report, _ = ReportTemplateReport.objects.update_or_create(
            service_visit_item=item,
            defaults={
                "template": template,
                "values": values,
                "narrative_text": narrative_text,
                "status": "submitted" if submit else "draft",
            },
        )

        try:
            if submit:
                transition_item_status(item, "PENDING_VERIFICATION", request.user)
            else:
                if item.status in ["REGISTERED", "RETURNED_FOR_CORRECTION"]:
                    transition_item_status(item, "IN_PROGRESS", request.user)
        except (ValidationError, PermissionDenied) as e:
            # Log the failure but still save the report to avoid data loss
            logger.warning(
                f"Report saved for item {item.id}, but status transition failed: {e}"
            )

        serializer = ReportTemplateReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)
