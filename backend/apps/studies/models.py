import uuid
from django.db import models
from django.conf import settings

STUDY_STATUS = (
    ("registered", "Registered"),
    ("in_progress", "In Progress"),
    ("draft", "Draft"),
    ("final", "Final"),
    ("delivered", "Delivered"),
)

class Study(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accession = models.CharField(max_length=30, unique=True)
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="studies")
    service = models.ForeignKey("catalog.Service", on_delete=models.PROTECT, related_name="studies")
    indication = models.CharField(max_length=300, blank=True, default="")
    status = models.CharField(max_length=20, choices=STUDY_STATUS, default="registered")
    performed_by = models.CharField(max_length=120, blank=True, default="")
    reported_by = models.CharField(max_length=120, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["accession"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.accession} - {self.patient.name} - {self.service.name}"
