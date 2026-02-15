import uuid
from django.db import models, transaction


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrn = models.CharField(max_length=30, unique=True, editable=False)
    patient_reg_no = models.CharField(max_length=30, unique=True, editable=False, null=True, blank=True, db_index=True, help_text="Permanent patient registration number")
    name = models.CharField(max_length=200)
    age = models.PositiveIntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)  # Added DOB support
    gender = models.CharField(max_length=20, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=300, blank=True, default="")
    referrer = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mrn"]),
            models.Index(fields=["patient_reg_no"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["name"]),
        ]

    def save(self, *args, **kwargs):
        if not self.mrn or not self.patient_reg_no:
            from apps.sequences.models import get_next_mrn, get_next_patient_reg_no
            with transaction.atomic():
                if not self.mrn:
                    self.mrn = get_next_mrn()
                if not self.patient_reg_no:
                    self.patient_reg_no = get_next_patient_reg_no()
        super().save(*args, **kwargs)

    def __str__(self):
        reg_no = self.patient_reg_no or self.mrn
        return f"{reg_no} - {self.name}"
