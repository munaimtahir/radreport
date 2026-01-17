from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0006_migrate_service_catalog_to_catalog_service"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReceiptSnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("receipt_number", models.CharField(db_index=True, max_length=20)),
                ("issued_at", models.DateTimeField()),
                ("items_json", models.JSONField(default=list, help_text="[{name, qty, unit_price, line_total}]")),
                ("subtotal", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("discount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("total_paid", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("payment_method", models.CharField(choices=[("cash", "Cash"), ("card", "Card"), ("online", "Online"), ("insurance", "Insurance"), ("other", "Other")], default="cash", max_length=20)),
                ("patient_name", models.CharField(blank=True, default="", max_length=200)),
                ("patient_phone", models.CharField(blank=True, default="", max_length=30)),
                ("patient_reg_no", models.CharField(blank=True, default="", max_length=30)),
                ("patient_mrn", models.CharField(blank=True, default="", max_length=30)),
                ("patient_age", models.CharField(blank=True, default="", max_length=20)),
                ("patient_gender", models.CharField(blank=True, default="", max_length=20)),
                ("cashier_name", models.CharField(blank=True, default="", max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("service_visit", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="receipt_snapshot", to="workflow.servicevisit")),
            ],
            options={
                "ordering": ["-issued_at"],
            },
        ),
        migrations.AddIndex(
            model_name="receiptsnapshot",
            index=models.Index(fields=["receipt_number"], name="workflow_re_receipt_4ee260_idx"),
        ),
        migrations.AddIndex(
            model_name="receiptsnapshot",
            index=models.Index(fields=["issued_at"], name="workflow_re_issued__922eff_idx"),
        ),
    ]
