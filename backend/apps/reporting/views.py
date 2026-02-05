import hashlib
import json
import logging
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.workflow.models import ServiceVisitItem
from .models import (
    ReportActionLogV2,
    ReportBlockLibrary,
    ReportInstanceV2,
    ReportPublishSnapshotV2,
    ReportTemplateV2,
    ServiceReportTemplateV2,
)
from .serializers import (
    ReportBlockLibrarySerializer,
    ReportInstanceV2Serializer,
    ReportTemplateV2Serializer,
    ServiceReportTemplateV2Serializer,
)
from .services.narrative_v2 import generate_narrative_v2
from .pdf_engine.report_pdf_v2 import generate_report_pdf_v2

logger = logging.getLogger(__name__)


class ReportTemplateV2ViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplateV2.objects.all()
    serializer_class = ReportTemplateV2Serializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_frozen:
            return Response({"error": "Template is frozen."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        instance = self.get_object()
        if instance.status == "active":
            return Response({"status": "already_active"})

        conflicts = ReportTemplateV2.objects.filter(
            code=instance.code,
            status="active",
        ).exclude(id=instance.id)
        force = request.query_params.get("force")
        if conflicts.exists() and not force:
            return Response(
                {"error": "Active template with same code exists."},
                status=status.HTTP_409_CONFLICT,
            )
        if conflicts.exists():
            conflicts.update(status="archived")

        instance.status = "active"
        instance.save(update_fields=["status", "updated_at"])
        return Response({"status": "active"})


class ServiceReportTemplateV2ViewSet(viewsets.ModelViewSet):
    queryset = ServiceReportTemplateV2.objects.all()
    serializer_class = ServiceReportTemplateV2Serializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        instance = self.get_object()
        if not instance.is_active:
            return Response({"error": "Cannot set inactive template as default."}, status=400)
        ServiceReportTemplateV2.objects.filter(service=instance.service).update(is_default=False)
        instance.is_default = True
        instance.save(update_fields=["is_default"])
        return Response({"status": "default_set"})


class ReportBlockLibraryViewSet(viewsets.ModelViewSet):
    queryset = ReportBlockLibrary.objects.all()
    serializer_class = ReportBlockLibrarySerializer
    permission_classes = [IsAuthenticated]


class ReportWorkItemViewSet(viewsets.ViewSet):
    """
    Endpoints for reporting on a specific ServiceVisitItem (V2 only).
    """

    permission_classes = [IsAuthenticated]

    def _get_item(self, pk):
        return get_object_or_404(ServiceVisitItem, pk=pk)

    def _get_v2_template(self, item):
        mapping = (
            ServiceReportTemplateV2.objects.select_related("template")
            .filter(
                service=item.service,
                is_active=True,
                is_default=True,
                template__status="active",
            )
            .first()
        )
        if not mapping:
            # V2-ONLY ENFORCEMENT
            data = {
                "error": "NO_ACTIVE_V2_TEMPLATE",
                "detail": "No active default TemplateV2 is mapped to this service. Reporting is V2-only.",
                "service_id": str(item.service.id),
                "service_code": item.service.code
            }
            # Custom 409 exception
            exc = exceptions.APIException(detail=data)
            exc.status_code = status.HTTP_409_CONFLICT
            exc.default_code = "conflict"
            raise exc
        return mapping.template

    def _get_or_create_instance(self, item, template, user):
        instance, created = ReportInstanceV2.objects.get_or_create(
            work_item=item,
            defaults={
                "template_v2": template,
                "created_by": user,
                "status": "draft",
            },
        )
        if not created and instance.template_v2_id != template.id:
            instance.template_v2 = template
            instance.save(update_fields=["template_v2", "updated_at"])
        if instance.created_by is None:
            instance.created_by = user
            instance.save(update_fields=["created_by"])
        return instance

    @action(detail=True, methods=["get"])
    def schema(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        return Response(
            {
                "schema_version": "v2",
                "template": {
                    "id": str(template_v2.id),
                    "code": template_v2.code,
                    "name": template_v2.name,
                    "modality": template_v2.modality,
                    "status": template_v2.status,
                },
                "json_schema": template_v2.json_schema,
                "ui_schema": template_v2.ui_schema,
            }
        )

    @action(detail=True, methods=["get"])
    def values(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        serializer = ReportInstanceV2Serializer(instance)
        last_snapshot = instance.publish_snapshots_v2.order_by("-version").first()
        return Response(
            {
                "schema_version": "v2",
                "values_json": serializer.data["values_json"],
                "narrative_json": serializer.data.get("narrative_json", {}),
                "status": serializer.data.get("status"),
                "last_saved_at": serializer.data.get("updated_at"),
                "is_published": instance.is_published,
                "last_published_at": last_snapshot.published_at if last_snapshot else None,
            }
        )

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        values_json = request.data.get("values_json")
        if not isinstance(values_json, dict):
            raise exceptions.ValidationError("values_json must be an object.")

        instance = self._get_or_create_instance(item, template_v2, request.user)
        if instance.status in ["submitted", "verified"]:
            return Response({"error": "Report is locked. Reset to draft to edit."}, status=409)

        narrative_json = request.data.get("narrative_json")
        instance.template_v2 = template_v2
        instance.values_json = values_json
        if narrative_json is not None:
            instance.narrative_json = narrative_json
        instance.status = "draft"
        instance.save()

        ReportActionLogV2.objects.create(
            report_v2=instance,
            action="save_draft",
            actor=request.user,
        )
        return Response({"schema_version": "v2", "saved": True, "narrative_json": instance.narrative_json})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        if instance.status != "draft":
            return Response({"error": "Only draft reports can be submitted."}, status=409)

        with transaction.atomic():
            instance.status = "submitted"
            instance.save(update_fields=["status", "updated_at"])
            item.status = "PENDING_VERIFICATION"
            item.submitted_at = timezone.now()
            item.save(update_fields=["status", "submitted_at"])
            ReportActionLogV2.objects.create(
                report_v2=instance,
                action="submit",
                actor=request.user,
            )
        return Response({"status": "submitted"})

    @action(detail=True, methods=["post"], url_path="generate-narrative")
    def generate_narrative(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        narrative_json = generate_narrative_v2(template_v2, instance.values_json)
        instance.narrative_json = narrative_json
        instance.save(update_fields=["narrative_json", "updated_at"])
        return Response({"schema_version": "v2", "status": instance.status, "narrative_json": narrative_json})

    @action(detail=True, methods=["get"], url_path="narrative")
    def narrative(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        return Response({"schema_version": "v2", "status": instance.status, "narrative_json": instance.narrative_json})

    @action(detail=True, methods=["get"], url_path="report-pdf")
    def report_pdf(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        narrative_json = generate_narrative_v2(template_v2, instance.values_json)
        pdf_bytes = generate_report_pdf_v2(str(instance.id), narrative_json)
        filename = f"Report_{item.service_visit.visit_id}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=["post"], url_path="return-for-correction")
    def return_for_correction(self, request, pk=None):
        item = self._get_item(pk)
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can return reports.")
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response({"error": "Reason is required."}, status=400)

        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        if instance.status not in ["submitted", "verified"]:
            return Response({"error": "Report can only be returned if submitted or verified."}, status=409)

        with transaction.atomic():
            instance.status = "draft"
            instance.save(update_fields=["status", "updated_at"])
            item.status = "RETURNED_FOR_CORRECTION"
            item.save(update_fields=["status"])
            ReportActionLogV2.objects.create(
                report_v2=instance,
                action="return",
                actor=request.user,
                meta={"reason": reason},
            )
        return Response({"status": "returned"})

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        item = self._get_item(pk)
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can verify reports.")
        notes = request.data.get("notes", "")

        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        if instance.status != "submitted":
            return Response({"error": "Only submitted reports can be verified."}, status=409)

        with transaction.atomic():
            instance.status = "verified"
            instance.save(update_fields=["status", "updated_at"])
            ReportActionLogV2.objects.create(
                report_v2=instance,
                action="verify",
                actor=request.user,
                meta={"notes": notes},
            )
        return Response({"status": "verified"})

    def _perform_publish_v2(self, instance_v2, user):
        template_v2 = instance_v2.template_v2
        narrative_json = generate_narrative_v2(template_v2, instance_v2.values_json)
        last_snapshot = instance_v2.publish_snapshots_v2.order_by("-version").first()
        version = (last_snapshot.version + 1) if last_snapshot else 1

        hash_input = json.dumps(
            {
                "template_id": str(template_v2.id),
                "template_version": str(template_v2.updated_at),
                "values_json": instance_v2.values_json,
                "narrative_json": narrative_json,
            },
            sort_keys=True,
        )
        content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        pdf_bytes = generate_report_pdf_v2(str(instance_v2.id), narrative_json)
        file_name = f"Report_V2_{instance_v2.work_item.service_visit.visit_id}_v{version}.pdf"

        snapshot = ReportPublishSnapshotV2(
            report_instance_v2=instance_v2,
            template_v2=template_v2,
            values_json=instance_v2.values_json,
            narrative_json=narrative_json,
            content_hash=content_hash,
            published_by=user,
            version=version,
        )
        snapshot.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
        snapshot.save()

        item = instance_v2.work_item
        item.status = "PUBLISHED"
        item.published_at = timezone.now()
        item.save(update_fields=["status", "published_at"])

        return version, snapshot

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        item = self._get_item(pk)
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can publish reports.")

        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        if instance.status != "verified":
            return Response({"error": "Only verified reports can be published."}, status=403)

        with transaction.atomic():
            version, snapshot = self._perform_publish_v2(instance, request.user)
            ReportActionLogV2.objects.create(
                report_v2=instance,
                action="publish",
                actor=request.user,
                meta={"version": version, "sha256": snapshot.content_hash},
            )

        return Response(
            {
                "status": "published",
                "version": version,
                "schema_version": "v2",
                "snapshot_id": str(snapshot.id),
                "content_hash": snapshot.content_hash,
                "pdf_url": request.build_absolute_uri(snapshot.pdf_file.url) if snapshot.pdf_file else None,
            }
        )

    @action(detail=True, methods=["get"], url_path="publish-history")
    def publish_history(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        snapshots = instance.publish_snapshots_v2.order_by("-version")
        history = []
        for snap in snapshots:
            history.append(
                {
                    "version": snap.version,
                    "published_at": snap.published_at,
                    "published_by": snap.published_by.username if snap.published_by else "Unknown",
                    "sha256": snap.content_hash,
                    "notes": "",
                    "pdf_url": request.build_absolute_uri(snap.pdf_file.url) if snap.pdf_file else None,
                }
            )
        return Response(history)

    @action(detail=True, methods=["get"], url_path="published-pdf")
    def published_pdf(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        version = request.query_params.get("version")
        if version:
            snapshot = instance.publish_snapshots_v2.filter(version=version).first()
            if not snapshot:
                raise exceptions.NotFound("Snapshot not found.")
        else:
            snapshot = instance.publish_snapshots_v2.order_by("-version").first()
            if not snapshot:
                raise exceptions.NotFound("No published snapshots found.")

        if not snapshot.pdf_file:
            raise exceptions.NotFound("PDF file missing for this snapshot.")

        response = HttpResponse(snapshot.pdf_file.read(), content_type="application/pdf")
        filename = f"Report_V2_{item.service_visit.visit_id}_v{snapshot.version}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=["get"], url_path="published-integrity")
    def published_integrity(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        instance = self._get_or_create_instance(item, template_v2, request.user)
        version = request.query_params.get("version")
        if not version:
            return Response({"error": "Version required"}, status=400)
        snapshot = instance.publish_snapshots_v2.filter(version=version).first()
        if not snapshot:
            raise exceptions.NotFound("Snapshot not found.")
        return Response(
            {
                "version": snapshot.version,
                "content_hash": snapshot.content_hash,
                "published_at": snapshot.published_at,
            }
        )
