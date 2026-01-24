import uuid
from django.db import models

class Modality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)  # USG, XRAY, CT
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code}"

class Service(models.Model):
    CATEGORY_CHOICES = [
        ("Radiology", "Radiology"),
        ("Lab", "Lab"),
        ("OPD", "OPD"),
        ("Procedure", "Procedure"),
    ]
    
    TAT_UNIT_CHOICES = [
        ("hours", "Hours"),
        ("days", "Days"),
    ]
    
    # Default turnaround time in minutes (1 hour)
    DEFAULT_TAT_MINUTES = 60

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)  # CSV-driven unique code
    modality = models.ForeignKey(Modality, on_delete=models.PROTECT, related_name="services")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Radiology")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Alias for price, CSV-driven")
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Legacy price alias")
    tat_value = models.PositiveIntegerField(default=1, help_text="TAT numeric value")
    tat_unit = models.CharField(max_length=10, choices=TAT_UNIT_CHOICES, default="hours")
    tat_minutes = models.PositiveIntegerField(default=DEFAULT_TAT_MINUTES, help_text="Calculated TAT in minutes")
    turnaround_time = models.PositiveIntegerField(default=DEFAULT_TAT_MINUTES, help_text="Legacy turnaround time in minutes")
    requires_radiologist_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("modality", "name")
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        # Sync charges to price if charges is set
        # Use explicit None checks to handle Decimal('0') correctly
        if self.charges is not None and self.price is None:
            self.price = self.charges
        elif self.price is not None and self.charges is None:
            self.charges = self.price
        if self.default_price is not None and self.price is None:
            self.price = self.default_price
        elif self.price is not None and self.default_price is None:
            self.default_price = self.price
        
        # Calculate tat_minutes from tat_value and tat_unit (or legacy turnaround_time)
        # For new instances with legacy turnaround_time set, use it to initialize tat_minutes
        if not self.pk and self.turnaround_time is not None and self.turnaround_time != self.DEFAULT_TAT_MINUTES:
            # New instance with explicit turnaround_time - use it
            self.tat_minutes = self.turnaround_time
        else:
            # Calculate from tat_value and tat_unit
            if self.tat_unit == "hours":
                self.tat_minutes = self.tat_value * 60
            elif self.tat_unit == "days":
                self.tat_minutes = self.tat_value * 24 * 60
        # Keep turnaround_time in sync
        self.turnaround_time = self.tat_minutes
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.modality.code} - {self.name}"
