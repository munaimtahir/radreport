from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Template, TemplateVersion, TemplateSection, TemplateField, FieldOption
from .serializers import TemplateSerializer, TemplateVersionSerializer

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
