from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import (
    Template, TemplateVersion, TemplateSection, TemplateField, FieldOption,
    ReportTemplate, ReportTemplateField, ReportTemplateFieldOption,
)
from .serializers import (
    TemplateSerializer, TemplateVersionSerializer,
    ReportTemplateSerializer, ReportTemplateFieldSerializer,
)

def build_schema(template: Template) -> dict:
    # Freeze a simple JSON schema snapshot from current editable template objects
    schema = {"template_id": str(template.id), "name": template.name, "modality_code": template.modality_code, "sections": []}
    for sec in template.sections.all().order_by("order"):
        sec_obj = {"id": str(sec.id), "title": sec.title, "order": sec.order, "fields": []}
        for f in sec.fields.all().order_by("order"):
            field_obj = {
                "id": str(f.id),
                "label": f.label,
                "key": f.key,
                "type": f.field_type,
                "required": f.required,
                "help_text": f.help_text,
                "placeholder": f.placeholder,
                "unit": f.unit,
                "order": f.order,
                "options": [{"label": o.label, "value": o.value, "order": o.order} for o in f.options.all().order_by("order")]
            }
            sec_obj["fields"].append(field_obj)
        schema["sections"].append(sec_obj)
    return schema

class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.prefetch_related("sections__fields__options").all()
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "modality_code"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        template = self.get_object()
        latest = template.versions.order_by("-version").first()
        next_version = 1 if not latest else latest.version + 1
        schema = build_schema(template)
        tv = TemplateVersion.objects.create(template=template, version=next_version, schema=schema, is_published=True)
        return Response(TemplateVersionSerializer(tv).data, status=status.HTTP_201_CREATED)

class TemplateVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TemplateVersion.objects.select_related("template").all()
    serializer_class = TemplateVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["template__name", "template__modality_code"]


class ReportTemplateViewSet(viewsets.ModelViewSet):
    queryset = ReportTemplate.objects.prefetch_related("fields__options").all()
    serializer_class = ReportTemplateSerializer
    search_fields = ["name", "code", "category"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("include_inactive") != "true":
            queryset = queryset.filter(is_active=True)
        return queryset

    def destroy(self, request, *args, **kwargs):
        template = self.get_object()
        template.is_active = False
        template.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        template = self.get_object()
        cloned = ReportTemplate.objects.create(
            name=f"{template.name} (Copy)",
            code=None,
            description=template.description,
            category=template.category,
            is_active=template.is_active,
            version=template.version,
        )
        for field in template.fields.all():
            new_field = ReportTemplateField.objects.create(
                template=cloned,
                label=field.label,
                key=field.key,
                field_type=field.field_type,
                is_required=field.is_required,
                help_text=field.help_text,
                default_value=field.default_value,
                placeholder=field.placeholder,
                order=field.order,
                validation=field.validation,
                is_active=field.is_active,
            )
            for opt in field.options.all():
                ReportTemplateFieldOption.objects.create(
                    field=new_field,
                    value=opt.value,
                    label=opt.label,
                    order=opt.order,
                    is_active=opt.is_active,
                )
        serializer = self.get_serializer(cloned)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["put"], url_path="fields")
    def update_fields(self, request, pk=None):
        template = self.get_object()
        fields_payload = request.data if isinstance(request.data, list) else request.data.get("fields", [])
        if not isinstance(fields_payload, list):
            return Response({"detail": "fields must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        existing_fields = {str(field.id): field for field in template.fields.all()}
        seen_field_ids = set()

        for idx, field_data in enumerate(fields_payload):
            field_data = dict(field_data)
            field_id = field_data.get("id")
            field_data.setdefault("order", idx)
            if field_id and str(field_id) in existing_fields:
                field = existing_fields[str(field_id)]
                serializer = ReportTemplateFieldSerializer(field, data=field_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                seen_field_ids.add(str(field_id))
            else:
                serializer = ReportTemplateFieldSerializer(data=field_data, context={"template": template})
                serializer.is_valid(raise_exception=True)
                created_field = serializer.save()
                seen_field_ids.add(str(created_field.id))

        for field in template.fields.exclude(id__in=seen_field_ids):
            field.is_active = False
            field.save(update_fields=["is_active"])

        template.refresh_from_db()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
