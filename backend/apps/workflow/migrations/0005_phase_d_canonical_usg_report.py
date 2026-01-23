# PHASE D: Canonical Ultrasound Reporting Standard
# Adds all canonical template fields to USGReport model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0004_phase_b_c_combined'),
    ]

    operations = [
        # PHASE D: Add canonical template fields to USGReport
        migrations.AddField(
            model_name='usgreport',
            name='report_status',
            field=models.CharField(choices=[('DRAFT', 'Draft'), ('FINAL', 'Final'), ('AMENDED', 'Amended')], db_index=True, default='DRAFT', help_text='DRAFT | FINAL | AMENDED', max_length=20),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='study_title',
            field=models.CharField(blank=True, default='', help_text='Auto-generated from service/study type', max_length=200),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='referring_clinician',
            field=models.CharField(blank=True, default='', help_text='Referring clinician name', max_length=200),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='clinical_history',
            field=models.TextField(blank=True, default='', help_text='Clinical history/indication (required before FINAL)'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='clinical_questions',
            field=models.TextField(blank=True, default='', help_text='Explicit clinical questions (multiline text)'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='exam_datetime',
            field=models.DateTimeField(blank=True, help_text='When exam was performed', null=True),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='report_datetime',
            field=models.DateTimeField(blank=True, help_text='When report was created/finalized', null=True),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='study_type',
            field=models.CharField(blank=True, choices=[('Abdomen', 'Abdomen'), ('Pelvis', 'Pelvis'), ('KUB', 'KUB'), ('OB', 'OB'), ('Doppler', 'Doppler'), ('Other', 'Other')], default='', help_text='Abdomen / Pelvis / KUB / OB / Doppler / Other', max_length=50),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='technique_approach',
            field=models.CharField(blank=True, default='', help_text='e.g., transabdominal, transvaginal', max_length=100),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='doppler_used',
            field=models.BooleanField(default=False, help_text='Doppler used in exam'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='contrast_used',
            field=models.BooleanField(default=False, help_text='Contrast used in exam'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='technique_notes',
            field=models.TextField(blank=True, default='', help_text='Additional technique notes'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='performed_by',
            field=models.ForeignKey(blank=True, help_text='User who performed the exam', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='performed_usg_reports', to='auth.user'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='interpreted_by',
            field=models.ForeignKey(blank=True, help_text='User who interpreted the exam', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interpreted_usg_reports', to='auth.user'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='comparison',
            field=models.TextField(blank=True, default='', help_text='Comparison with prior studies'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='scan_quality',
            field=models.CharField(blank=True, choices=[('Good', 'Good'), ('Fair', 'Fair'), ('Limited', 'Limited')], default='', help_text='Good/Fair/Limited - REQUIRED before FINAL', max_length=20),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='limitations_text',
            field=models.TextField(blank=True, default='', help_text="Scan limitations - REQUIRED before FINAL (can be 'None' but must be explicit)"),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='findings_json',
            field=models.JSONField(default=dict, help_text='Structured per-organ modules with standardized keys'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='measurements_json',
            field=models.JSONField(default=list, help_text='Optional summary table derived from findings OR stored as structured list'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='impression_text',
            field=models.TextField(blank=True, default='', help_text='Impression - REQUIRED before FINAL'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='suggestions_text',
            field=models.TextField(blank=True, default='', help_text='Suggestions or follow-up recommendations'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='critical_flag',
            field=models.BooleanField(default=False, help_text='Urgent/critical result flag'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='critical_communication_json',
            field=models.JSONField(default=dict, help_text='{ recipient, method, communicated_at, notes } - REQUIRED if critical_flag true'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='signoff_json',
            field=models.JSONField(default=dict, help_text='{ clinician_name, credentials, verified_at } set on FINAL/AMENDED'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='version',
            field=models.PositiveIntegerField(default=1, help_text='Increment on each FINAL/AMENDED publish; DRAFT saves do not increment'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='parent_report_id',
            field=models.UUIDField(blank=True, help_text='Link to parent report if this is an amendment', null=True),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='amendment_reason',
            field=models.TextField(blank=True, default='', help_text='Reason for amendment'),
        ),
        migrations.AddField(
            model_name='usgreport',
            name='amendment_history_json',
            field=models.JSONField(default=list, help_text='Immutable history of finalized versions'),
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='usgreport',
            index=models.Index(fields=['report_status'], name='workflow_us_report_s_idx'),
        ),
        migrations.AddIndex(
            model_name='usgreport',
            index=models.Index(fields=['version'], name='workflow_us_version_idx'),
        ),
    ]
