import uuid
from django.db import models

FIELD_TYPES = (
    ("short_text", "Short Text"),
    ("number", "Number"),
    ("dropdown", "Dropdown (single)"),
    ("checklist", "Checklist (multi)"),
    ("paragraph", "Paragraph"),
    ("boolean", "Yes/No"),
)

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    modality_code = models.CharField(max_length=20, blank=True, default="")  # USG/XRAY/CT etc
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "modality_code")

    def __str__(self):
        return f"{self.name} ({self.modality_code})"

class TemplateVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    schema = models.JSONField(default=dict)  # frozen schema snapshot for this version
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        unique_together = ("template", "version")
        ordering = ["-version"]

    def __str__(self):
        return f"{self.template.name} v{self.version}"

class TemplateSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.template.name} :: {self.title}"

class TemplateField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(TemplateSection, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=200)
    key = models.SlugField(max_length=80)  # used in values JSON
    field_type = models.CharField(max_length=30, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    help_text = models.CharField(max_length=300, blank=True, default="")
    placeholder = models.CharField(max_length=200, blank=True, default="")
    unit = models.CharField(max_length=30, blank=True, default="")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("section", "key")
        ordering = ["order"]

    def __str__(self):
        return f"{self.section.title} :: {self.label}"

class FieldOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(TemplateField, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=120)
    value = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.field.key}: {self.label}"
