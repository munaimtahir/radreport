import uuid
from django.db import models
from django.utils import timezone

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

    def generate_mrn(self):
        """Generate a unique MR number based on date and sequence"""
        import time
        now = timezone.now()
        prefix = now.strftime("%Y%m%d")
        # Get count of patients today to append sequence number
        today_count = Patient.objects.filter(mrn__startswith=f"MR{prefix}").count()
        sequence = str(today_count + 1).zfill(4)
        mrn = f"MR{prefix}{sequence}"
        
        # Handle race condition: if MRN exists, try next sequence
        max_attempts = 100
        attempt = 0
        while Patient.objects.filter(mrn=mrn).exists() and attempt < max_attempts:
            today_count += 1
            sequence = str(today_count + 1).zfill(4)
            mrn = f"MR{prefix}{sequence}"
            attempt += 1
        
        return mrn

    def generate_patient_reg_no(self):
        """Generate a permanent unique patient registration number"""
        now = timezone.now()
        # Use a simple sequential format: PRN followed by sequential number
        # Get the highest existing patient_reg_no
        last_patient = Patient.objects.exclude(patient_reg_no__isnull=True).order_by('-patient_reg_no').first()
        if last_patient and last_patient.patient_reg_no:
            try:
                # Extract number from format like PRN000001
                last_num = int(last_patient.patient_reg_no.replace('PRN', ''))
                next_num = last_num + 1
            except (ValueError, AttributeError):
                next_num = 1
        else:
            next_num = 1
        
        patient_reg_no = f"PRN{str(next_num).zfill(6)}"
        
        # Handle race condition
        max_attempts = 100
        attempt = 0
        while Patient.objects.filter(patient_reg_no=patient_reg_no).exists() and attempt < max_attempts:
            next_num += 1
            patient_reg_no = f"PRN{str(next_num).zfill(6)}"
            attempt += 1
        
        return patient_reg_no

    def save(self, *args, **kwargs):
        if not self.mrn:
            self.mrn = self.generate_mrn()
        if not self.patient_reg_no:
            self.patient_reg_no = self.generate_patient_reg_no()
        super().save(*args, **kwargs)

    def __str__(self):
        reg_no = self.patient_reg_no or self.mrn
        return f"{reg_no} - {self.name}"
