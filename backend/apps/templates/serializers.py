from rest_framework import serializers
from .models import Template, TemplateVersion, TemplateSection, TemplateField, FieldOption

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
