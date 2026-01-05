from rest_framework import serializers
from .models import Template, TemplateVersion, TemplateSection, TemplateField, FieldOption

class FieldOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldOption
        fields = ["id", "label", "value", "order"]

class TemplateFieldSerializer(serializers.ModelSerializer):
    options = FieldOptionSerializer(many=True, required=False)
    class Meta:
        model = TemplateField
        fields = ["id","label","key","field_type","required","help_text","placeholder","unit","order","options"]

class TemplateSectionSerializer(serializers.ModelSerializer):
    fields = TemplateFieldSerializer(many=True, required=False)
    class Meta:
        model = TemplateSection
        fields = ["id","title","order","fields"]

class TemplateSerializer(serializers.ModelSerializer):
    sections = TemplateSectionSerializer(many=True, required=False)
    class Meta:
        model = Template
        fields = ["id","name","modality_code","is_active","created_at","sections"]

class TemplateVersionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    class Meta:
        model = TemplateVersion
        fields = ["id","template","template_name","version","schema","created_at","is_published"]
