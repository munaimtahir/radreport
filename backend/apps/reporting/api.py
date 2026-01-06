from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.http import FileResponse, Http404
from .models import Report
from .serializers import ReportSerializer
from .pdf import build_basic_pdf
from apps.templates.models import TemplateVersion
from apps.studies.models import Study
from apps.audit.models import AuditLog

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related("study","study__patient","study__service","template_version").all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["study__accession", "study__patient__name", "study__service__name"]
    filterset_fields = ["status", "study__service__modality__code"]

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
