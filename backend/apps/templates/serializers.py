from rest_framework import serializers
from .models import (
    Template, TemplateVersion, TemplateSection, TemplateField, FieldOption,
    ReportTemplate, ReportTemplateField, ReportTemplateFieldOption, ServiceReportTemplate,
)

class FieldOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldOption
        fields = ["id", "label", "value", "order"]

    def create(self, validated_data):
        field = self.context["field"]
        return FieldOption.objects.create(field=field, **validated_data)

class TemplateFieldSerializer(serializers.ModelSerializer):
    options = FieldOptionSerializer(many=True, required=False)
    class Meta:
        model = TemplateField
        fields = ["id","label","key","field_type","required","help_text","placeholder","unit","order","options"]

    def create(self, validated_data):
        section = self.context["section"]
        options_data = validated_data.pop("options", [])
        field = TemplateField.objects.create(section=section, **validated_data)
        for opt_data in options_data:
            FieldOptionSerializer(context={"field": field}).create(opt_data)
        return field

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if options_data is not None:
            instance.options.all().delete()
            for opt_data in options_data:
                FieldOptionSerializer(context={"field": instance}).create(opt_data)
        return instance

class TemplateSectionSerializer(serializers.ModelSerializer):
    fields = TemplateFieldSerializer(many=True, required=False)
    class Meta:
        model = TemplateSection
        fields = ["id","title","order","fields"]

    def create(self, validated_data):
        template = self.context["template"]
        fields_data = validated_data.pop("fields", [])
        section = TemplateSection.objects.create(template=template, **validated_data)
        for field_data in fields_data:
            TemplateFieldSerializer(context={"section": section}).create(field_data)
        return section

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if fields_data is not None:
            instance.fields.all().delete()
            for field_data in fields_data:
                TemplateFieldSerializer(context={"section": instance}).create(field_data)
        return instance

class TemplateSerializer(serializers.ModelSerializer):
    sections = TemplateSectionSerializer(many=True, required=False)
    class Meta:
        model = Template
        fields = ["id","name","modality_code","is_active","created_at","sections"]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        template = Template.objects.create(**validated_data)
        for section_data in sections_data:
            TemplateSectionSerializer(context={"template": template}).create(section_data)
        return template

    def update(self, instance, validated_data):
        sections_data = validated_data.pop("sections", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if sections_data is not None:
            instance.sections.all().delete()
            for section_data in sections_data:
                TemplateSectionSerializer(context={"template": instance}).create(section_data)
        return instance

class TemplateVersionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    class Meta:
        model = TemplateVersion
        fields = ["id","template","template_name","version","schema","created_at","is_published"]


class ReportTemplateFieldOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplateFieldOption
        fields = ["id", "label", "value", "order", "is_active"]

    def create(self, validated_data):
        field = self.context["field"]
        return ReportTemplateFieldOption.objects.create(field=field, **validated_data)


class ReportTemplateFieldSerializer(serializers.ModelSerializer):
    options = ReportTemplateFieldOptionSerializer(many=True, required=False)

    class Meta:
        model = ReportTemplateField
        fields = [
            "id", "label", "key", "field_type", "is_required", "help_text",
            "default_value", "placeholder", "order", "validation", "is_active", "options",
        ]

    def create(self, validated_data):
        template = self.context["template"]
        options_data = validated_data.pop("options", [])
        field = ReportTemplateField.objects.create(template=template, **validated_data)
        for opt_data in options_data:
            ReportTemplateFieldOptionSerializer(context={"field": field}).create(opt_data)
        return field

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            instance.options.all().update(is_active=False)
            for opt_data in options_data:
                opt_id = opt_data.get("id")
                if opt_id:
                    opt = instance.options.filter(id=opt_id).first()
                    if opt:
                        for attr, value in opt_data.items():
                            setattr(opt, attr, value)
                        opt.is_active = opt_data.get("is_active", True)
                        opt.save()
                        continue
                ReportTemplateFieldOptionSerializer(context={"field": instance}).create(opt_data)
        return instance


class ReportTemplateSerializer(serializers.ModelSerializer):
    fields = ReportTemplateFieldSerializer(many=True, required=False)

    class Meta:
        model = ReportTemplate
        fields = [
            "id", "name", "code", "description", "category", "is_active",
            "version", "created_at", "updated_at", "fields",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        template = ReportTemplate.objects.create(**validated_data)
        for field_data in fields_data:
            ReportTemplateFieldSerializer(context={"template": template}).create(field_data)
        return template

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if fields_data is not None:
            instance.fields.all().update(is_active=False)
            for field_data in fields_data:
                field_id = field_data.get("id")
                if field_id:
                    field = instance.fields.filter(id=field_id).first()
                    if field:
                        ReportTemplateFieldSerializer().update(field, field_data)
                        continue
                ReportTemplateFieldSerializer(context={"template": instance}).create(field_data)
        return instance


class ReportTemplateSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = ["id", "name", "code", "category", "is_active", "version"]


class ReportTemplateDetailSerializer(serializers.ModelSerializer):
    fields = ReportTemplateFieldSerializer(many=True, read_only=True)

    class Meta:
        model = ReportTemplate
        fields = [
            "id", "name", "code", "description", "category", "is_active",
            "version", "created_at", "updated_at", "fields",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        active_fields = [field for field in data.get("fields", []) if field.get("is_active", True)]
        for field in active_fields:
            field["options"] = [opt for opt in field.get("options", []) if opt.get("is_active", True)]
        data["fields"] = active_fields
        return data


class ServiceReportTemplateSerializer(serializers.ModelSerializer):
    template = ReportTemplateSummarySerializer(read_only=True)
    template_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = ServiceReportTemplate
        fields = ["id", "service", "template", "template_id", "is_default", "is_active", "created_at"]
        read_only_fields = ["created_at", "template", "service"]
