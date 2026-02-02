from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_service_default_price_turnaround_time'),
        ('reporting', '0007_template_governance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportTemplateV2',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('code', models.CharField(max_length=80, help_text='Slug-like template code')),
                ('name', models.CharField(max_length=200)),
                ('modality', models.CharField(max_length=20, help_text='Modality code, e.g., USG')),
                ('version', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('json_schema', models.JSONField()),
                ('ui_schema', models.JSONField(blank=True, default=dict)),
                ('narrative_rules', models.JSONField(blank=True, default=dict)),
                ('meta', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_report_templates_v2', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('code', 'version'), name='unique_template_v2_code_version')],
            },
        ),
        migrations.CreateModel(
            name='ServiceReportTemplateV2',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_templates_v2', to='catalog.service')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_links', to='reporting.reporttemplatev2')),
            ],
            options={
                'unique_together': {('service', 'template')},
            },
        ),
    ]
