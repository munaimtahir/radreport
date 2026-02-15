"""
Concurrency-safe DB-level sequence counters for ID generation.
Supports MRN, patient_reg, service_visit, receipt with period-based resets.
"""
from django.db import models, transaction


class SequenceCounter(models.Model):
    """DB-level sequence counter. Key + period uniquely identifies a counter."""
    key = models.CharField(max_length=50)  # patient_mrn, patient_reg, service_visit, receipt
    period = models.CharField(max_length=16)  # YYYYMMDD, YY, YYMM
    value = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "period"], name="unique_seq_key_period")
        ]
        indexes = [
            models.Index(fields=["key", "period"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.key}/{self.period}: {self.value}"

    @classmethod
    def next_value(cls, key: str, period: str, increment: bool = True) -> int:
        """
        Get next sequence value. Uses select_for_update for concurrency safety.
        If increment=False, returns current+1 without persisting (for dry_run/preview).
        """
        with transaction.atomic():
            row, created = cls.objects.select_for_update().get_or_create(
                key=key,
                period=period,
                defaults={"value": 0},
            )
            next_val = row.value + 1
            if increment:
                row.value = next_val
                row.save(update_fields=["value", "updated_at"])
            return next_val


def get_next_mrn() -> str:
    """Format: MRYYYYMMDD#### (daily reset)."""
    from django.utils import timezone
    period = timezone.now().strftime("%Y%m%d")
    seq = SequenceCounter.next_value("patient_mrn", period)
    return f"MR{period}{seq:04d}"


def get_next_patient_reg_no() -> str:
    """Format: CCJ-YY-#### (yearly reset)."""
    from django.utils import timezone
    period = timezone.now().strftime("%y")
    seq = SequenceCounter.next_value("patient_reg", period)
    return f"CCJ-{period}-{seq:04d}"


def get_next_visit_id() -> str:
    """Format: YYMM-#### (monthly reset)."""
    from django.utils import timezone
    period = timezone.now().strftime("%y%m")
    seq = SequenceCounter.next_value("service_visit", period)
    return f"{period}-{seq:04d}"


def get_next_receipt_number(increment: bool = True) -> str:
    """Format: YYMM-#### (monthly reset). increment=False for dry_run preview."""
    from django.utils import timezone
    period = timezone.now().strftime("%y%m")
    seq = SequenceCounter.next_value("receipt", period, increment=increment)
    return f"{period}-{seq:04d}"
