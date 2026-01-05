import uuid
from django.db import models

class Modality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)  # USG, XRAY, CT
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code}"

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modality = models.ForeignKey(Modality, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tat_minutes = models.PositiveIntegerField(default=60)
    default_template = models.ForeignKey("templates.Template", on_delete=models.SET_NULL, null=True, blank=True)
    requires_radiologist_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("modality", "name")

    def __str__(self):
        return f"{self.modality.code} - {self.name}"
