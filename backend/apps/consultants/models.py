import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError


class ConsultantProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    degrees = models.CharField(max_length=200, blank=True, default="", help_text="e.g. MBBS, FCPS")
    designation = models.CharField(max_length=100, blank=True, default="", help_text="e.g. Consultant Radiologist")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultant_profiles",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["display_name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.display_name


class ConsultantBillingRule(models.Model):
    RULE_TYPE_PERCENT_SPLIT = "PERCENT_SPLIT"
    RULE_TYPE_FIXED_AMOUNT = "FIXED_AMOUNT"
    RULE_TYPE_CHOICES = (
        (RULE_TYPE_PERCENT_SPLIT, "Percent Split"),
        (RULE_TYPE_FIXED_AMOUNT, "Fixed Amount"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultant = models.ForeignKey(
        ConsultantProfile,
        on_delete=models.CASCADE,
        related_name="billing_rules",
    )
    # If service is null, it's the global default for this consultant
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.CASCADE,
        related_name="consultant_billing_rules",
        null=True,
        blank=True,
        help_text="Specific service override. If blank, applies to all services not otherwise specified."
    )
    rule_type = models.CharField(
        max_length=50,
        choices=RULE_TYPE_CHOICES,
        default=RULE_TYPE_PERCENT_SPLIT,
    )
    consultant_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
        null=True,
        blank=True,
    )
    consultant_fixed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    active_from = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-active_from", "-created_at"]
        indexes = [
            models.Index(fields=["consultant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.consultant.display_name} - {self.consultant_percent}%"


class ConsultantSettlement(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_FINALIZED = "FINALIZED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = (
        (STATUS_DRAFT, "Draft"),
        (STATUS_FINALIZED, "Finalized"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultant = models.ForeignKey(
        ConsultantProfile,
        on_delete=models.PROTECT,
        related_name="settlements",
    )
    date_from = models.DateField()
    date_to = models.DateField()
    gross_collected = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    net_payable = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    clinic_share = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_consultant_settlements",
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consultant", "status"]),
            models.Index(fields=["date_from", "date_to"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = ConsultantSettlement.objects.get(pk=self.pk)
            if previous.status == self.STATUS_FINALIZED:
                raise ValidationError("Finalized settlements are immutable.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Settlement {self.id} - {self.consultant.display_name}"


class ConsultantSettlementLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    settlement = models.ForeignKey(
        ConsultantSettlement,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    service_item = models.ForeignKey(
        "workflow.ServiceVisitItem",
        on_delete=models.PROTECT,
        related_name="consultant_settlement_lines",
    )
    item_amount_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    consultant_share_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    clinic_share_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["settlement"]),
            models.Index(fields=["service_item"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding and self.settlement.status == ConsultantSettlement.STATUS_FINALIZED:
            raise ValidationError("Finalized settlement lines are immutable.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Settlement line {self.id}"
