# Generated manually for Phase 2

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reporting", "0008_reporting_v2_models"),
    ]

    operations = [
        # Add narrative_rules field to ReportTemplateV2
        migrations.AddField(
            model_name="reporttemplatev2",
            name="narrative_rules",
            field=models.JSONField(blank=True, default=dict, help_text="Narrative generation rules"),
        ),
        # Create ReportPublishSnapshotV2 model
        migrations.CreateModel(
            name="ReportPublishSnapshotV2",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("values_json", models.JSONField(help_text="Immutable values at publish time")),
                ("narrative_json", models.JSONField(help_text="Generated narrative at publish time")),
                ("pdf_file", models.FileField(upload_to="report_snapshots_v2/%Y/%m/%d/")),
                ("content_hash", models.CharField(db_index=True, help_text="SHA256 hash of template+values+narrative", max_length=64)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("published_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("report_instance_v2", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="publish_snapshots_v2", to="reporting.reportinstancev2")),
                ("template_v2", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="snapshots", to="reporting.reporttemplatev2")),
            ],
            options={
                "ordering": ["-version"],
                "unique_together": {("report_instance_v2", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="reportpublishsnapshotv2",
            index=models.Index(fields=["report_instance_v2", "published_at"], name="reporting_r_report__b8e9b5_idx"),
        ),
        migrations.AddIndex(
            model_name="reportpublishsnapshotv2",
            index=models.Index(fields=["content_hash"], name="reporting_r_content_c0a1f7_idx"),
        ),
    ]
