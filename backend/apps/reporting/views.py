import csv
import io
import json
import hashlib
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.http import HttpResponse
from rest_framework import viewsets, status, exceptions, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.catalog.models import Service
from apps.workflow.models import ServiceVisitItem, ServiceVisit
from .models import (
    ServiceReportProfile, ReportInstance, ReportValue,
    ReportProfile, ReportParameter, ReportParameterOption,
    ReportParameterLibraryItem, ReportProfileParameterLink,
    TemplateAuditLog, ReportTemplateV2, ServiceReportTemplateV2,
    ReportInstanceV2
)
from .serializers import (
    ReportProfileSerializer, ReportInstanceSerializer, ReportValueSerializer, ReportSaveSerializer,
    ReportParameterSerializer, ServiceReportProfileSerializer, ProfileListSerializer,
    ReportParameterLibraryItemSerializer, ReportInstanceV2Serializer,
    ReportTemplateV2Serializer, ServiceReportTemplateV2Serializer,
)

class ReportParameterLibraryItemViewSet(viewsets.ModelViewSet):
    queryset = ReportParameterLibraryItem.objects.all()
    serializer_class = ReportParameterLibraryItemSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    search_fields = ["name", "slug", "modality"]
    filterset_fields = ["modality"]
from .services.narrative_v1 import generate_report_narrative
from .pdf_engine.report_pdf import generate_report_pdf
from .models import ReportPublishSnapshot, ReportActionLog
from .utils import parse_bool
from django.core.files.base import ContentFile
from .governance_views import log_audit

class ReportProfileViewSet(viewsets.ModelViewSet):
    queryset = ReportProfile.objects.all()
    serializer_class = ReportProfileSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    search_fields = ["code", "name", "modality"]
    filterset_fields = ["modality", "is_active", "status", "is_frozen"]

    def get_queryset(self):
        """
        Override to support filtering by status and code for version management.
        """
        queryset = super().get_queryset()
        
        # Filter by code (for viewing versions)
        code = self.request.query_params.get("code")
        if code:
            queryset = queryset.filter(code=code)
        
        # Default to showing only active versions in list if not filtering
        if self.action == "list" and not self.request.query_params.get("status"):
            show_all = self.request.query_params.get("show_all", "").lower() == "true"
            if not show_all:
                queryset = queryset.filter(status="active")
        
        return queryset.order_by("code", "-version")

    def get_serializer_class(self):
        """Use lightweight serializer for list view."""
        if self.action == "list":
            return ProfileListSerializer
        return super().get_serializer_class()

    def perform_update(self, serializer):
        """
        Check if profile can be edited before updating.
        Frozen or active profiles with reports cannot be edited.
        """
        instance = self.get_object()
        can_edit, reason = instance.can_edit()
        
        if not can_edit:
            raise exceptions.PermissionDenied(
                f"Cannot edit this template: {reason}. "
                "Clone the template to create a new draft version for editing."
            )
        
        serializer.save()
        
        # Log audit for edits
        log_audit(
            self.request.user,
            "edit",
            "report_profile",
            instance.id,
            {"version": instance.version, "code": instance.code}
        )

    def perform_destroy(self, instance):
        """
        Prevent hard delete for production safety.
        Only allow delete for non-active profiles without reports.
        """
        can_delete, reason = instance.can_delete()
        
        if not can_delete:
            # Log the blocked delete attempt
            log_audit(
                self.request.user,
                "delete_blocked",
                "report_profile",
                instance.id,
                {"reason": reason, "version": instance.version, "code": instance.code}
            )
            raise exceptions.PermissionDenied(
                f"Cannot delete this template: {reason}. "
                "Archive the template instead."
            )
        
        instance.delete()

    def _format_options(self, options):
        opts = []
        for option in options:
            label = option.get("label") if isinstance(option, dict) else option.label
            value = option.get("value") if isinstance(option, dict) else option.value
            if label == value:
                opts.append(value)
            else:
                opts.append(f"{label}:{value}")
        return ", ".join(opts)

    def _parse_options(self, options_raw):
        if not options_raw:
            return []
        delimiter = "|" if "|" in options_raw else ","
        options_list = []
        for opt in options_raw.split(delimiter):
            opt = opt.strip()
            if not opt:
                continue
            if ":" in opt:
                lbl, val = opt.split(":", 1)
                options_list.append({"label": lbl.strip(), "value": val.strip()})
            else:
                options_list.append({"label": opt, "value": opt})
        return options_list

    @action(detail=False, methods=["get"], url_path="template-csv")
    def template_csv(self, request):
        fieldnames = ["code", "name", "modality", "is_active"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "code": "USG_KUB",
            "name": "USG KUB",
            "modality": "USG",
            "is_active": "true",
        })
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report_profiles_template.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        fieldnames = ["code", "name", "modality", "is_active", "enable_narrative", "narrative_mode"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for profile in ReportProfile.objects.all().order_by("code"):
            writer.writerow({
                "code": profile.code,
                "name": profile.name,
                "modality": profile.modality,
                "is_active": profile.is_active,
                "enable_narrative": profile.enable_narrative,
                "narrative_mode": profile.narrative_mode,
            })

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report_profiles_export.csv"'
        return response

    def _process_parameters_import(self, profile, rows):
        errors = []
        preview = []
        created_count = 0
        updated_count = 0

        for idx, row in enumerate(rows, start=2):
            try:
                slug = row.get("slug")
                if not slug:
                    raise ValueError("slug is required")

                action = "create"
                if ReportParameter.objects.filter(profile=profile, slug=slug).exists():
                    action = "update"

                preview.append({
                    "action": action,
                    "slug": slug,
                    "name": row.get("name"),
                    "section": row.get("section"),
                    "parameter_type": row.get("parameter_type"),
                })
                if action == "create":
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        return {"created": created_count, "updated": updated_count, "errors": errors, "preview": preview}

    @action(detail=True, methods=["post"], url_path="import-parameters")
    def import_parameters(self, request, pk=None):
        profile = self.get_object()
        if "file" not in request.FILES:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        dry_run = parse_bool(request.query_params.get("dry_run", "true"))
        
        decoded_file = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_file))
        rows = list(reader)

        if dry_run:
            result = self._process_parameters_import(profile, rows)
            status_code = status.HTTP_400_BAD_REQUEST if result["errors"] else status.HTTP_200_OK
            return Response(result, status=status_code)

        created_fields = 0
        updated_fields = 0
        errors = []

        with transaction.atomic():
            for row in rows:
                try:
                    field_data = {
                        "section": row.get("section", ""),
                        "name": row.get("name") or row.get("slug"),
                        "parameter_type": row["parameter_type"],
                        "unit": row.get("unit") or None,
                        "normal_value": row.get("normal_value") or None,
                        "order": int(row["order"]) if row.get("order") else 0,
                        "is_required": parse_bool(row.get("is_required", ""), default=False),
                        "sentence_template": row.get("sentence_template") or None,
                        "narrative_role": row.get("narrative_role") or "finding",
                        "omit_if_values": json.loads(row["omit_if_values_json"]) if row.get("omit_if_values_json") else None,
                        "join_label": row.get("join_label") or None,
                    }
                    slug = row["slug"]
                    options_list = self._parse_options(row.get("options", ""))

                    param, created = ReportParameter.objects.update_or_create(
                        profile=profile,
                        slug=slug,
                        defaults=field_data,
                    )
                    if field_data["parameter_type"] in ["dropdown", "checklist"]:
                        param.options.all().delete()
                        for i, opt in enumerate(options_list):
                            ReportParameterOption.objects.create(
                                parameter=param, label=opt["label"], value=opt["value"], order=i
                            )
                    else:
                        param.options.all().delete()

                    if created:
                        created_fields += 1
                    else:
                        updated_fields += 1
                except Exception as e:
                    errors.append({"slug": row.get("slug"), "error": str(e)})
            
            if errors:
                transaction.set_rollback(True)
                return Response({"created": 0, "updated": 0, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"fields_created": created_fields, "fields_updated": updated_fields})

    @action(detail=True, methods=["get", "post"], url_path="parameters-csv")
    def parameters_csv(self, request, pk=None):
        if request.method == "POST":
            return self.import_parameters(request, pk)

        # GET: Export parameters for this profile
        profile = self.get_object()
        fieldnames = [
            "profile_code", "section", "name", "slug", 
            "parameter_type", "unit", "normal_value", "is_required", "order",
            "options", "sentence_template", "narrative_role",
            "omit_if_values_json", "join_label"
        ]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        params = ReportParameter.objects.filter(profile=profile).prefetch_related("options").order_by("order")
        for param in params:
            options_str = self._format_options(param.options.all())
            writer.writerow({
                "profile_code": profile.code,
                "section": param.section,
                "name": param.name,
                "slug": param.slug,
                "parameter_type": param.parameter_type,
                "unit": param.unit or "",
                "normal_value": param.normal_value or "",
                "is_required": "true" if param.is_required else "false",
                "order": param.order,
                "options": options_str,
                "sentence_template": param.sentence_template or "",
                "narrative_role": param.narrative_role,
                "omit_if_values_json": json.dumps(param.omit_if_values) if param.omit_if_values else "",
                "join_label": param.join_label or "",
            })

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{profile.code}_parameters.csv"'
        return response

    @action(detail=True, methods=["post"], url_path="reorder-parameters")
    def reorder_parameters(self, request, pk=None):
        """
        Reorders parameters for a profile.
        Expects a list of {id: <uuid>, order: <int>}
        Supports both legacy parameters and library links.
        """
        profile = self.get_object()
        new_orders = request.data.get("orders", [])
        
        if not isinstance(new_orders, list):
            return Response({"error": "orders must be a list"}, status=400)
            
        with transaction.atomic():
            for item in new_orders:
                item_id = item.get("id")
                order = item.get("order")
                
                # Check legacy params first
                param = profile.parameters.filter(id=item_id).first()
                if param:
                    param.order = order
                    param.save()
                    continue
                    
                # Check library links
                link = profile.library_links.filter(id=item_id).first()
                if link:
                    link.order = order
                    link.save()
        
        return Response({"status": "reordered"})

    def _process_profile_import(self, rows):
        created = 0
        updated = 0
        errors = []
        preview = []
        for idx, row in enumerate(rows, start=2):
            try:
                code = row.get("code")
                if not code:
                    raise ValueError("code is required")
                
                action = "create"
                if ReportProfile.objects.filter(code=code).exists():
                    action = "update"
                
                preview.append({"action": action, "code": code, "name": row.get("name")})
                if action == "create":
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})
        return {"created": created, "updated": updated, "errors": errors, "preview": preview}

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        if "file" not in request.FILES:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        dry_run = parse_bool(request.query_params.get("dry_run", "true"))
        
        decoded_file = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_file))
        rows = list(reader)

        if dry_run:
            result = self._process_profile_import(rows)
            status_code = status.HTTP_400_BAD_REQUEST if result["errors"] else status.HTTP_200_OK
            return Response(result, status=status_code)

        created_profiles = 0
        updated_profiles = 0
        errors = []

        with transaction.atomic():
            for row in rows:
                try:
                    code = row["code"]
                    defaults = {
                        "name": row["name"],
                        "modality": row["modality"],
                        "is_active": parse_bool(row.get("is_active"), default=True),
                        "enable_narrative": parse_bool(row.get("enable_narrative"), default=True),
                        "narrative_mode": row.get("narrative_mode", "rule_based"),
                    }
                    _, created = ReportProfile.objects.update_or_create(code=code, defaults=defaults)
                    if created:
                        created_profiles += 1
                    else:
                        updated_profiles += 1
                except Exception as e:
                    errors.append({"code": code, "error": str(e)})

            if errors:
                transaction.set_rollback(True)
                return Response({"created": 0, "updated": 0, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"profiles_created": created_profiles, "profiles_updated": updated_profiles})


class ReportTemplateV2ViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplateV2.objects.all()
    serializer_class = ReportTemplateV2Serializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    search_fields = ["code", "name", "modality"]
    filterset_fields = ["code", "modality", "status"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(
            self.request.user,
            "create",
            "report_template_v2",
            instance.id,
            {"code": instance.code},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(
            self.request.user,
            "edit",
            "report_template_v2",
            instance.id,
            {"code": instance.code},
        )

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        template = self.get_object()
        force = parse_bool(request.query_params.get("force", "false"))
        allow_reactivate = parse_bool(request.query_params.get("allow_reactivate", "false"))

        if template.status == "archived" and not allow_reactivate:
            return Response(
                {"detail": "Archived templates cannot be reactivated without allow_reactivate=1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conflicts = ReportTemplateV2.objects.filter(
            code=template.code,
            modality=template.modality,
            status="active",
        ).exclude(id=template.id)

        if conflicts.exists() and not force:
            return Response(
                {"detail": "Another active template exists for this code and modality."},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            if conflicts.exists() and force:
                conflicts.update(status="archived")
            serializer = self.get_serializer(
                template,
                data={"status": "active"},
                partial=True,
                context={"allow_reactivate": allow_reactivate},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        log_audit(
            request.user,
            "activate",
            "report_template_v2",
            template.id,
            {"code": template.code, "force": force},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class ReportParameterViewSet(viewsets.ModelViewSet):
    queryset = ReportParameter.objects.all()
    serializer_class = ReportParameterSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ["profile", "section"]
    ordering_fields = ["order"]

    csv_fieldnames = [
        "profile_code", "section", "name", "slug", 
        "parameter_type", "unit", "normal_value", "is_required", "order",
        "options", "sentence_template", "narrative_role",
        "omit_if_values_json", "join_label"
    ]

    def _format_options(self, options):
        opts = []
        for option in options:
            label = option.label
            value = option.value
            if label == value:
                opts.append(value)
            else:
                opts.append(f"{label}:{value}")
        return ", ".join(opts)

    def _parse_options(self, options_raw):
        if not options_raw:
            return []
        delimiter = "|" if "|" in options_raw else ","
        options_list = []
        for opt in options_raw.split(delimiter):
            opt = opt.strip()
            if not opt:
                continue
            if ":" in opt:
                lbl, val = opt.split(":", 1)
                options_list.append({"label": lbl.strip(), "value": val.strip()})
            else:
                options_list.append({"label": opt, "value": opt})
        return options_list

    @action(detail=False, methods=["get"], url_path="template-csv")
    def template_csv(self, request):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.csv_fieldnames)
        writer.writeheader()
        writer.writerow({
            "profile_code": "USG_KUB",
            "section": "Kidneys",
            "name": "Right Kidney Size",
            "slug": "right_kidney_size",
            "parameter_type": "number",
            "unit": "mm",
            "normal_value": "100",
            "is_required": "true",
            "order": "1",
            "options": "",
            "sentence_template": "{name}: {value}{unit}.",
            "narrative_role": "finding",
            "omit_if_values_json": "[]",
            "join_label": "",
        })
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report_parameters_template.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.csv_fieldnames)
        writer.writeheader()

        params = ReportParameter.objects.all().select_related("profile").prefetch_related("options").order_by("profile__code", "order")
        for param in params:
            options_str = self._format_options(param.options.all())
            writer.writerow({
                "profile_code": param.profile.code,
                "section": param.section,
                "name": param.name,
                "slug": param.slug,
                "parameter_type": param.parameter_type,
                "unit": param.unit or "",
                "normal_value": param.normal_value or "",
                "is_required": "true" if param.is_required else "false",
                "order": param.order,
                "options": options_str,
                "sentence_template": param.sentence_template or "",
                "narrative_role": param.narrative_role,
                "omit_if_values_json": json.dumps(param.omit_if_values) if param.omit_if_values else "",
                "join_label": param.join_label or "",
            })

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report_parameters_export.csv"'
        return response
    
    def _process_parameters_import(self, rows):
        errors = []
        preview = []
        created_count = 0
        updated_count = 0
        
        profile_codes = {r.get("profile_code") for r in rows if r.get("profile_code")}
        profiles = {p.code: p for p in ReportProfile.objects.filter(code__in=profile_codes)}

        for idx, row in enumerate(rows, start=2):
            try:
                profile_code = row.get("profile_code")
                slug = row.get("slug")
                if not profile_code or not slug:
                    raise ValueError("profile_code and slug are required")
                
                profile = profiles.get(profile_code)
                if not profile:
                    raise ValueError(f"Profile with code {profile_code} not found")

                action = "create"
                if ReportParameter.objects.filter(profile=profile, slug=slug).exists():
                    action = "update"

                preview.append({
                    "action": action,
                    "profile_code": profile_code,
                    "slug": slug,
                    "name": row.get("name"),
                })
                if action == "create":
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        return {"created": created_count, "updated": updated_count, "errors": errors, "preview": preview}

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request, pk=None):
        if "file" not in request.FILES:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        dry_run = parse_bool(request.query_params.get("dry_run", "true"))
        
        decoded_file = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_file))
        rows = list(reader)

        if dry_run:
            result = self._process_parameters_import(rows)
            status_code = status.HTTP_400_BAD_REQUEST if result["errors"] else status.HTTP_200_OK
            return Response(result, status=status_code)

        created_fields = 0
        updated_fields = 0
        errors = []
        
        profile_codes = {r.get("profile_code") for r in rows if r.get("profile_code")}
        profiles = {p.code: p for p in ReportProfile.objects.filter(code__in=profile_codes)}

        with transaction.atomic():
            for row in rows:
                try:
                    profile_code = row.get("profile_code")
                    profile = profiles.get(profile_code)
                    if not profile:
                        raise ValueError(f"Profile with code {profile_code} not found")

                    field_data = {
                        "section": row.get("section", ""),
                        "name": row.get("name") or row.get("slug"),
                        "parameter_type": row["parameter_type"],
                        "unit": row.get("unit") or None,
                        "normal_value": row.get("normal_value") or None,
                        "order": int(row["order"]) if row.get("order") else 0,
                        "is_required": parse_bool(row.get("is_required", ""), default=False),
                        "sentence_template": row.get("sentence_template") or None,
                        "narrative_role": row.get("narrative_role") or "finding",
                        "omit_if_values": json.loads(row["omit_if_values_json"]) if row.get("omit_if_values_json") else None,
                        "join_label": row.get("join_label") or None,
                    }
                    slug = row["slug"]
                    options_list = self._parse_options(row.get("options", ""))

                    param, created = ReportParameter.objects.update_or_create(
                        profile=profile,
                        slug=slug,
                        defaults=field_data,
                    )
                    if field_data["parameter_type"] in ["dropdown", "checklist"]:
                        param.options.all().delete()
                        for i, opt in enumerate(options_list):
                            ReportParameterOption.objects.create(
                                parameter=param, label=opt["label"], value=opt["value"], order=i
                            )
                    else:
                        param.options.all().delete()

                    if created:
                        created_fields += 1
                    else:
                        updated_fields += 1
                except Exception as e:
                    errors.append({"slug": row.get("slug"), "error": str(e)})
            
            if errors:
                transaction.set_rollback(True)
                return Response({"created": 0, "updated": 0, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"fields_created": created_fields, "fields_updated": updated_fields})

    def perform_create(self, serializer):
        instance = serializer.save()
        self._handle_options(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._handle_options(instance)

    def _handle_options(self, instance):
        options_data = self.request.data.get("options")
        if options_data is not None and isinstance(options_data, list):
            with transaction.atomic():
                # Replace options logic: delete existing and create new?
                # Or smart update? For simplicity, delete and recreate since IDs might be temp
                # But we should preserve IDs if possible?
                # The frontend sends "id" if existing.

                existing_ids = [opt.get("id") for opt in options_data if opt.get("id")]
                # Delete those not in list
                instance.options.exclude(id__in=existing_ids).delete()

                for opt in options_data:
                    oid = opt.get("id")
                    label = opt.get("label", "")
                    value = opt.get("value", "")
                    order = opt.get("order", 0)

                    if oid:
                        # Fix IDOR: scope update to instance's options only
                        instance.options.filter(id=oid).update(
                            label=label, value=value, order=order
                        )
                    else:
                        ReportParameterOption.objects.create(
                            parameter=instance,
                            label=label,
                            value=value,
                            order=order
                        )

class ServiceReportProfileViewSet(viewsets.ModelViewSet):
    queryset = ServiceReportProfile.objects.all()
    serializer_class = ServiceReportProfileSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ["service", "profile"]
    csv_fieldnames = [
        "service_id", "service_code", "service_name",
        "profile_id", "profile_code", "profile_name",
        "enforce_single_profile", "is_default"
    ]

    @action(detail=False, methods=["get"], url_path="template-csv")
    def template_csv(self, request):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.csv_fieldnames)
        writer.writeheader()
        writer.writerow({
            "service_id": "",
            "service_code": "XR-CHEST",
            "service_name": "Chest X-Ray",
            "profile_id": "",
            "profile_code": "XR_CHEST",
            "profile_name": "X-Ray Chest",
            "enforce_single_profile": "true",
            "is_default": "true",
        })
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="service_template_links_template.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.csv_fieldnames)
        writer.writeheader()
        links = self.get_queryset().select_related("service", "profile")
        for link in links:
            writer.writerow({
                "service_id": link.service_id,
                "service_code": link.service.code or "",
                "service_name": link.service.name,
                "profile_id": link.profile_id,
                "profile_code": link.profile.code,
                "profile_name": link.profile.name,
                "enforce_single_profile": str(link.enforce_single_profile).lower(),
                "is_default": str(link.is_default).lower(),
            })
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="service_template_links_export.csv"'
        return response

    def _process_csv_import(self, rows):
        created = 0
        updated = 0
        errors = []
        preview = []

        service_codes = {r.get("service_code") for r in rows if r.get("service_code")}
        profile_codes = {r.get("profile_code") for r in rows if r.get("profile_code")}

        services = {s.code: s for s in Service.objects.filter(code__in=service_codes)}
        profiles = {p.code: p for p in ReportProfile.objects.filter(code__in=profile_codes)}

        for idx, row in enumerate(rows, start=2):
            service_code = row.get("service_code")
            profile_code = row.get("profile_code")

            service = services.get(service_code)
            profile = profiles.get(profile_code)

            if not service or not profile:
                errors.append({
                    "row": idx,
                    "error": "Service or profile not found",
                    "service_code": service_code,
                    "profile_code": profile_code,
                })
                continue

            action = "create"
            if ServiceReportProfile.objects.filter(service=service, profile=profile).exists():
                action = "update"
            
            preview.append({
                "action": action,
                "service_code": service_code,
                "profile_code": profile_code,
                "is_default": parse_bool(row.get("is_default"), default=True),
            })

            if action == "create":
                created += 1
            else:
                updated += 1

        return {"created": created, "updated": updated, "errors": errors, "preview": preview}

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "CSV file required"}, status=status.HTTP_400_BAD_REQUEST)
        if not file.name.endswith(".csv"):
            return Response({"detail": "File must be a CSV"}, status=status.HTTP_400_BAD_REQUEST)

        dry_run = parse_bool(request.query_params.get("dry_run", "true"))
        decoded_file = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded_file))
        rows = list(reader)

        if dry_run:
            result = self._process_csv_import(rows)
            status_code = status.HTTP_400_BAD_REQUEST if result["errors"] else status.HTTP_200_OK
            return Response(result, status=status_code)

        created = 0
        updated = 0
        errors = []
        
        with transaction.atomic():
            services_by_code = {s.code: s for s in Service.objects.filter(code__in={r.get("service_code") for r in rows if r.get("service_code")})}
            profiles_by_code = {p.code: p for p in ReportProfile.objects.filter(code__in={r.get("profile_code") for r in rows if r.get("profile_code")})}

            for idx, row in enumerate(rows, start=2):
                service = services_by_code.get(row.get("service_code"))
                profile = profiles_by_code.get(row.get("profile_code"))

                if not service or not profile:
                    errors.append({
                        "row": idx,
                        "error": "Service or profile not found",
                        "service_code": row.get("service_code"),
                        "profile_code": row.get("profile_code"),
                    })
                    continue

                enforce_single_profile = parse_bool(row.get("enforce_single_profile"), default=True)
                is_default = parse_bool(row.get("is_default"), default=True)

                link, was_created = ServiceReportProfile.objects.update_or_create(
                    service=service,
                    profile=profile,
                    defaults={
                        "enforce_single_profile": enforce_single_profile,
                        "is_default": is_default,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
        
            if errors:
                transaction.set_rollback(True)
                return Response({"created": 0, "updated": 0, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"created": created, "updated": updated, "errors": None})


class ServiceReportTemplateV2ViewSet(viewsets.ModelViewSet):
    queryset = ServiceReportTemplateV2.objects.all()
    serializer_class = ServiceReportTemplateV2Serializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ["service", "template", "is_active", "is_default"]

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.is_default and instance.is_active:
            ServiceReportTemplateV2.objects.filter(
                service=instance.service,
                is_default=True,
            ).exclude(id=instance.id).update(is_default=False)
        log_audit(
            self.request.user,
            "create",
            "service_template_v2",
            instance.id,
            {"service_id": str(instance.service_id), "template_id": str(instance.template_id)},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_default and instance.is_active:
            ServiceReportTemplateV2.objects.filter(
                service=instance.service,
                is_default=True,
            ).exclude(id=instance.id).update(is_default=False)
        log_audit(
            self.request.user,
            "edit",
            "service_template_v2",
            instance.id,
            {"service_id": str(instance.service_id), "template_id": str(instance.template_id)},
        )

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        link = self.get_object()
        if not link.is_active:
            return Response(
                {"detail": "Inactive template mappings cannot be default."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            ServiceReportTemplateV2.objects.filter(
                service=link.service,
                is_default=True,
            ).exclude(id=link.id).update(is_default=False)
            link.is_default = True
            link.save(update_fields=["is_default"])

        log_audit(
            request.user,
            "edit",
            "service_template_v2",
            str(link.id),
            {
                "service_id": str(link.service_id),
                "template_id": str(link.template_id),
                "set_default": True,
            },
        )
        serializer = self.get_serializer(link)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReportWorkItemViewSet(viewsets.ViewSet):
    """
    Endpoints for reporting on a specific ServiceVisitItem.
    Lookup field is 'pk' mapping to ServiceVisitItem.id
    """
    permission_classes = [IsAuthenticated]

    def _get_item(self, pk):
        return get_object_or_404(ServiceVisitItem, pk=pk)

    def _get_profile(self, item):
        # Find profile for the service
        # Logic: Check ServiceReportProfile first
        srp = ServiceReportProfile.objects.filter(service=item.service).first()
        if not srp:
            raise exceptions.NotFound("No report profile associated with this service.")
        return srp.profile

    def _get_v2_template(self, item):
        mapping = (
            ServiceReportTemplateV2.objects.select_related("template")
            .filter(service=item.service, is_active=True, template__status="active")
            .order_by("-is_default", "created_at")
            .first()
        )
        return mapping.template if mapping else None

    def _get_instance(self, item):
        try:
            return item.report_instance
        except ReportInstance.DoesNotExist:
            return None

    @action(detail=True, methods=["get"])
    def schema(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        if template_v2:
            return Response({
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
            })

        profile = self._get_profile(item)
        serializer = ReportProfileSerializer(profile)
        data = serializer.data
        data["schema_version"] = "v1"
        return Response(data)

    @action(detail=True, methods=["get"])
    def values(self, request, pk=None):
        item = self._get_item(pk)
        template_v2 = self._get_v2_template(item)
        if template_v2:
            instance, created = ReportInstanceV2.objects.get_or_create(
                work_item=item,
                defaults={
                    "template_v2": template_v2,
                    "created_by": request.user,
                    "status": "draft",
                },
            )
            if not created and instance.template_v2_id != template_v2.id:
                instance.template_v2 = template_v2
                instance.save(update_fields=["template_v2", "updated_at"])
            serializer = ReportInstanceV2Serializer(instance)
            return Response({
                "schema_version": "v2",
                "values_json": serializer.data["values_json"],
                "status": instance.status,
                "last_saved_at": instance.updated_at,
            })

        instance = self._get_instance(item)

        if not instance:
            return Response({
                "schema_version": "v1",
                "status": "draft",
                "values": [],
            })

        serializer = ReportValueSerializer(instance.values.all(), many=True)
        last_published = instance.publish_snapshots.order_by("-version").first()
        return Response({
            "schema_version": "v1",
            "status": instance.status,
            "is_published": instance.is_published,
            "values": serializer.data,
            "last_saved_at": instance.updated_at,
            "narrative_updated_at": instance.narrative_updated_at,
            "last_published_at": last_published.published_at if last_published else None,
        })

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        item = self._get_item(pk)
        schema_version = request.data.get("schema_version")
        if schema_version == "v2":
            template_v2 = self._get_v2_template(item)
            if not template_v2:
                raise exceptions.NotFound("No V2 report template associated with this service.")
            values_json = request.data.get("values_json")
            if not isinstance(values_json, dict):
                raise exceptions.ValidationError("values_json must be an object.")

            instance, created = ReportInstanceV2.objects.get_or_create(
                work_item=item,
                defaults={
                    "template_v2": template_v2,
                    "values_json": values_json,
                    "created_by": request.user,
                    "status": "draft",
                },
            )
            if not created:
                instance.template_v2 = template_v2
                instance.values_json = values_json
                if instance.created_by is None:
                    instance.created_by = request.user
                instance.status = "draft"
                instance.save()
            return Response({"schema_version": "v2", "saved": True})

        profile = self._get_profile(item)
        
        # Check if already submitted/verified (locked)
        instance = self._get_instance(item)
        if instance and instance.status in ["submitted", "verified"]:
            raise exceptions.PermissionDenied("Cannot edit a submitted report.")

        save_serializer = ReportSaveSerializer(data=request.data)
        save_serializer.is_valid(raise_exception=True)
        values_list = save_serializer.validated_data["values"]

        with transaction.atomic():
            if not instance:
                instance = ReportInstance.objects.create(
                    service_visit_item=item,
                    profile=profile,
                    created_by=request.user,
                    status="draft"
                )
            
            # Create a map of existing values: ID -> ReportValue obj
            # ID is either parameter.id or profile_link.id
            current_values = {}
            for v in instance.values.all():
                if v.parameter_id:
                    current_values[str(v.parameter_id)] = v
                if v.profile_link_id:
                    current_values[str(v.profile_link_id)] = v
            
            # Pre-fetch valid IDs for validation
            valid_param_ids = set(str(p.id) for p in profile.parameters.all())
            valid_link_ids = set(str(l.id) for l in profile.library_links.all())

            for item_data in values_list:
                param_id = str(item_data["parameter_id"])
                val = item_data["value"]
                
                # val might be list or string, save as string/JSON
                if isinstance(val, (list, dict)):
                    import json
                    val_str = json.dumps(val)
                else:
                    val_str = str(val) if val is not None else None

                # Determine type
                if param_id in valid_param_ids:
                    is_legacy = True
                elif param_id in valid_link_ids:
                    is_legacy = False
                else:
                    continue # Ignore invalid params
                
    
                if param_id in current_values:
                    rv = current_values[param_id]
                    rv.value = val_str
                    rv.save()
                else:
                    if is_legacy:
                        ReportValue.objects.create(
                            report=instance,
                            parameter_id=param_id,
                            value=val_str
                        )
                    else:
                        ReportValue.objects.create(
                            report=instance,
                            profile_link_id=param_id,
                            value=val_str
                        )

        return Response({"status": "saved", "report_id": instance.id})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)

        if not instance:
             profile = self._get_profile(item)
             instance = ReportInstance.objects.create(
                 service_visit_item=item,
                 profile=profile,
                 created_by=request.user,
                 status="draft"
             )

        if instance.status in ["submitted", "verified"]:
             return Response({"status": "already_submitted"})

        # Validation
        profile = instance.profile
        required_params = profile.parameters.filter(is_required=True)
        required_links = profile.library_links.filter(is_required=True)
        
        existing_values = {}
        for v in instance.values.all():
            val = v.value
            if v.parameter_id:
                existing_values[str(v.parameter_id)] = val
            if v.profile_link_id:
                existing_values[str(v.profile_link_id)] = val
        
        missing = []
        # Check legacy
        for rp in required_params:
            param_id_str = str(rp.id)
            if param_id_str not in existing_values or not existing_values[param_id_str]:
                missing.append({
                    "parameter_id": param_id_str,
                    "message": "Required"
                })
        # Check links
        for rl in required_links:
            link_id_str = str(rl.id)
            if link_id_str not in existing_values or not existing_values[link_id_str]:
                missing.append({
                    "parameter_id": link_id_str,
                    "message": "Required"
                })
        
        if missing:
            return Response({
                "error": "validation_failed", 
                "missing": missing
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            instance.status = "submitted"
            instance.save()
            
            # Update workflow status to PENDING_VERIFICATION
            item.status = "PENDING_VERIFICATION" 
            item.submitted_at = timezone.now()
            item.save()

        return Response({"status": "submitted"})

    @action(detail=True, methods=["post"], url_path="generate-narrative")
    def generate_narrative(self, request, pk=None):
        """
        Generates and saves the narrative.
        """
        item = self._get_item(pk)
        instance = self._get_instance(item)

        if not instance:
            raise exceptions.NotFound("Report must be started (saved as draft) before generating narrative.")

        # Logic per requirements: 
        # Allowed when report exists (draft or submitted).
        # We allow re-generation even if submitted/verified? 
        # Requirement: "When reportStatus is submitted/verified: Read-only already; still allow Generate Preview only if permitted (optional)"
        # Let's allow it. It updates the narrative fields in the DB.
        
        narrative_data = generate_report_narrative(str(instance.id))
        
        with transaction.atomic():
            instance.findings_text = narrative_data["findings_text"]
            instance.impression_text = narrative_data["impression_text"]
            instance.limitations_text = narrative_data["limitations_text"]
            instance.narrative_version = narrative_data["version"]
            instance.narrative_updated_at = timezone.now()
            instance.save()
            
        return Response({
            "status": instance.status,
            "narrative": narrative_data
        })

    @action(detail=True, methods=["get"], url_path="narrative")
    def narrative(self, request, pk=None):
        """
        Returns stored narrative fields.
        """
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
            return Response({
                "status": "draft",
                "narrative": {
                    "version": "v1",
                    "findings_text": "",
                    "impression_text": "",
                    "limitations_text": ""
                }
            })
            
        return Response({
            "status": instance.status,
            "narrative": {
                "version": instance.narrative_version,
                "findings_text": instance.findings_text or "",
                "impression_text": instance.impression_text or "",
                "limitations_text": instance.limitations_text or ""
            }
        })
    @action(detail=True, methods=["get"], url_path="report-pdf")
    def report_pdf(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report has not been started.")
             
        # Check permission? IsAuthenticated is on class.
        # User asked for "Read-only access allowed for submitted/verified reports"
        # "Draft allowed if explicitly requested (same endpoint)"
        # Since it is a GET request, it is read-only by definition.
        
        # Auto-generate narrative if empty?
        # Requirement: "If narrative not generated yet: Auto-generate narrative using Stage 2 engine; Persist it"
        if not instance.narrative_updated_at or not instance.findings_text:
             narrative_data = generate_report_narrative(str(instance.id))
             with transaction.atomic():
                instance.findings_text = narrative_data["findings_text"]
                instance.impression_text = narrative_data["impression_text"]
                instance.limitations_text = narrative_data["limitations_text"]
                instance.narrative_version = narrative_data["version"]
                instance.narrative_updated_at = timezone.now()
                instance.save()
        
        try:
            pdf_bytes = generate_report_pdf(str(instance.id))
        except Exception as e:
            # Log error?
            return Response({"error": f"Failed to generate PDF: {str(e)}"}, status=500)
            
        filename = f"Report_{item.service_visit.visit_id}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        # Content-Disposition: inline; filename="..."
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=["post"], url_path="return-for-correction")
    def return_for_correction(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
            raise exceptions.NotFound("Report not found.")
            
        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can return reports.")

        # Logic: Allowed only if submitted or verified
        if instance.status not in ["submitted", "verified"]:
            return Response({"error": "Report can only be returned if submitted or verified."}, status=409)

        reason = request.data.get("reason", "").strip()
        if not reason:
             return Response({"error": "Reason is required."}, status=400)

        with transaction.atomic():
            instance.status = "draft"
            instance.save()
            
            # Update workflow status if possible
            item.status = "RETURNED_FOR_CORRECTION"
            item.save()
            
            ReportActionLog.objects.create(
                report=instance,
                action="return",
                actor=request.user,
                meta={"reason": reason}
            )

        return Response({"status": "returned"})

    def _perform_publish(self, instance, user, notes=""):
        """
        Internal helper to execute the publish logic (snapshot, PDF, workflow update).
        Assumes we are inside a transaction.
        """
        # Ensure narrative exists
        if not instance.findings_text:
            from .services.narrative_v1 import generate_report_narrative
            narrative_data = generate_report_narrative(str(instance.id))
            instance.findings_text = narrative_data["findings_text"]
            instance.impression_text = narrative_data["impression_text"]
            instance.limitations_text = narrative_data["limitations_text"]
            instance.narrative_version = narrative_data["version"]
            instance.narrative_updated_at = timezone.now()
            instance.save()

        # Calculate next version
        last_snapshot = instance.publish_snapshots.order_by("-version").first()
        version = (last_snapshot.version + 1) if last_snapshot else 1

        # Generate JSON map
        values_map = {}
        existing_values = {str(v.parameter_id): v.value for v in instance.values.all() if v.parameter_id}
        # Also include profile_link values if any
        for v in instance.values.all():
            if v.profile_link_id:
                values_map[str(v.profile_link_id)] = v.value

        # Get all parameters from profile (legacy)
        for param in instance.profile.parameters.all():
            p_id = str(param.id)
            val = existing_values.get(p_id)
            if val is None:
                val = param.normal_value
            values_map[p_id] = val

        # Canonical JSON for hash
        import json
        import hashlib
        canonical_json = json.dumps(values_map, sort_keys=True)
        narrative_concat = (instance.findings_text or "") + (instance.impression_text or "") + (instance.limitations_text or "")
        hash_input = canonical_json + narrative_concat
        sha256_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

        # Generate PDF
        from .pdf_engine.report_pdf import generate_report_pdf
        pdf_bytes = generate_report_pdf(str(instance.id))
        file_name = f"Report_{instance.service_visit_item.service_visit.visit_id}_v{version}.pdf"

        snapshot = ReportPublishSnapshot(
            report=instance,
            version=version,
            published_by=user,
            findings_text=instance.findings_text or "",
            impression_text=instance.impression_text or "",
            limitations_text=instance.limitations_text or "",
            values_json=values_map,
            sha256=sha256_hash,
            notes=notes
        )
        snapshot.pdf_file.save(file_name, ContentFile(pdf_bytes), save=False)
        snapshot.save()

        # Update workflow status
        item = instance.service_visit_item
        item.status = "PUBLISHED"
        item.published_at = timezone.now()
        item.save()

        ReportActionLog.objects.create(
            report=instance,
            action="publish",
            actor=user,
            meta={"version": version, "sha256": sha256_hash, "notes": notes, "auto": True}
        )
        return version

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report not found.")

        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can verify reports.")

        if instance.status != "submitted":
             return Response({"error": "Only submitted reports can be verified."}, status=409)

        notes = request.data.get("notes", "")

        with transaction.atomic():
            # Ensure narrative exists
            if not instance.findings_text:
                from .services.narrative_v1 import generate_report_narrative
                narrative_data = generate_report_narrative(str(instance.id))
                instance.findings_text = narrative_data["findings_text"]
                instance.impression_text = narrative_data["impression_text"]
                instance.limitations_text = narrative_data["limitations_text"]
                instance.narrative_version = narrative_data["version"]
                instance.narrative_updated_at = timezone.now()
            
            instance.status = "verified"
            instance.save()
            
            # Log action
            ReportActionLog.objects.create(
                report=instance,
                action="verify",
                actor=request.user,
                meta={"notes": notes}
            )
            
            # AUTO PUBLISH
            version = self._perform_publish(instance, request.user, notes=f"Auto-published on verification. {notes}")
            
        return Response({"status": "verified", "published": True, "version": version})

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        
        if not instance:
             raise exceptions.NotFound("Report not found.")

        # Permission check: Verifier only
        if not (request.user.is_superuser or request.user.groups.filter(name="reporting_verifier").exists()):
            raise exceptions.PermissionDenied("Only verifiers can publish reports.")

        if instance.status not in ["verified", "published"]:
             return Response({"error": "Only verified reports can be published."}, status=409)

        notes = request.data.get("notes", "")

        with transaction.atomic():
            version = self._perform_publish(instance, request.user, notes)

        return Response({"status": "published", "version": version})

    @action(detail=True, methods=["get"], url_path="publish-history")
    def publish_history(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        if not instance:
             return Response([])
        
        snapshots = instance.publish_snapshots.all().order_by("-version")
        history = []
        for snap in snapshots:
            history.append({
                "version": snap.version,
                "published_at": snap.published_at,
                "published_by": snap.published_by.username if snap.published_by else "Unknown",
                "sha256": snap.sha256,
                "notes": snap.notes,
                "pdf_url": request.build_absolute_uri(snap.pdf_file.url) if snap.pdf_file else None
            })
        return Response(history)

    @action(detail=True, methods=["get"], url_path="published-pdf")
    def published_pdf(self, request, pk=None):
        item = self._get_item(pk)
        instance = self._get_instance(item)
        if not instance:
             raise exceptions.NotFound("Report not found.")
        
        version = request.query_params.get("version")
        if not version:
             return Response({"error": "Version required"}, status=400)
             
        try:
            snapshot = instance.publish_snapshots.get(version=version)
        except ReportPublishSnapshot.DoesNotExist:
             raise exceptions.NotFound("Snapshot not found.")
             
        if not snapshot.pdf_file:
             raise exceptions.NotFound("PDF file missing for this snapshot.")

        # Return file response
        response = HttpResponse(snapshot.pdf_file.read(), content_type='application/pdf')
        filename = f"Report_{item.service_visit.visit_id}_v{version}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
