# Generated manually for workflow app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0002_patient_date_of_birth_alter_patient_mrn'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceCatalog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('default_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('turnaround_time', models.PositiveIntegerField(default=60, help_text='Turnaround time in minutes')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ServiceVisit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('visit_id', models.CharField(db_index=True, editable=False, max_length=30, unique=True)),
                ('status', models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], db_index=True, default='REGISTERED', max_length=30)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_service_visits', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_service_visits', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='service_visits', to='patients.patient')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='service_visits', to='workflow.servicecatalog')),
            ],
            options={
                'ordering': ['-registered_at'],
            },
        ),
        migrations.CreateModel(
            name='StatusAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('from_status', models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], max_length=30)),
                ('to_status', models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], max_length=30)),
                ('reason', models.TextField(blank=True, default='', null=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('service_visit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_audit_logs', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['-changed_at'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('method', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('online', 'Online'), ('insurance', 'Insurance'), ('other', 'Other')], default='cash', max_length=20)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('received_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('service_visit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['-received_at'],
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('net_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('balance_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('service_visit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='invoice', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='USGReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('report_json', models.JSONField(default=dict, help_text='Structured report data')),
                ('saved_at', models.DateTimeField(auto_now=True)),
                ('published_pdf_path', models.CharField(blank=True, default='', max_length=500)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('return_reason', models.TextField(blank=True, default='')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_usg_reports', to=settings.AUTH_USER_MODEL)),
                ('service_visit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='usg_report', to='workflow.servicevisit')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_usg_reports', to=settings.AUTH_USER_MODEL)),
                ('verifier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_usg_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-saved_at'],
            },
        ),
        migrations.CreateModel(
            name='OPDVitals',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bp_systolic', models.PositiveIntegerField(blank=True, null=True)),
                ('bp_diastolic', models.PositiveIntegerField(blank=True, null=True)),
                ('pulse', models.PositiveIntegerField(blank=True, null=True)),
                ('temperature', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('respiratory_rate', models.PositiveIntegerField(blank=True, null=True)),
                ('spo2', models.PositiveIntegerField(blank=True, help_text='SpO2 percentage', null=True)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('height', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('bmi', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('entered_at', models.DateTimeField(auto_now_add=True)),
                ('entered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('service_visit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='opd_vitals', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['-entered_at'],
            },
        ),
        migrations.CreateModel(
            name='OPDConsult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('diagnosis', models.TextField(blank=True, default='')),
                ('notes', models.TextField(blank=True, default='')),
                ('medicines_json', models.JSONField(default=list, help_text='List of medicines prescribed')),
                ('investigations_json', models.JSONField(default=list, help_text='List of investigations ordered')),
                ('advice', models.TextField(blank=True, default='')),
                ('followup', models.CharField(blank=True, default='', max_length=200)),
                ('consult_at', models.DateTimeField(auto_now_add=True)),
                ('published_pdf_path', models.CharField(blank=True, default='', max_length=500)),
                ('consultant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='opd_consults', to=settings.AUTH_USER_MODEL)),
                ('service_visit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='opd_consult', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['-consult_at'],
            },
        ),
        migrations.AddIndex(
            model_name='servicevisit',
            index=models.Index(fields=['visit_id'], name='workflow_se_visit_i_idx'),
        ),
        migrations.AddIndex(
            model_name='servicevisit',
            index=models.Index(fields=['status'], name='workflow_se_status_idx'),
        ),
        migrations.AddIndex(
            model_name='servicevisit',
            index=models.Index(fields=['patient'], name='workflow_se_patient_idx'),
        ),
        migrations.AddIndex(
            model_name='servicevisit',
            index=models.Index(fields=['service'], name='workflow_se_service_idx'),
        ),
        migrations.AddIndex(
            model_name='servicevisit',
            index=models.Index(fields=['registered_at'], name='workflow_se_registe_idx'),
        ),
        migrations.AddIndex(
            model_name='statusauditlog',
            index=models.Index(fields=['service_visit'], name='workflow_st_service_idx'),
        ),
        migrations.AddIndex(
            model_name='statusauditlog',
            index=models.Index(fields=['changed_at'], name='workflow_st_changed_idx'),
        ),
        migrations.AddIndex(
            model_name='servicecatalog',
            index=models.Index(fields=['code'], name='workflow_se_code_idx'),
        ),
        migrations.AddIndex(
            model_name='servicecatalog',
            index=models.Index(fields=['is_active'], name='workflow_se_is_acti_idx'),
        ),
    ]
