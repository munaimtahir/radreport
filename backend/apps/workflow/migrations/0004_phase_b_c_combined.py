# Combined migration for Phase B + Phase C
# This migration includes Phase B (ServiceVisitItem creation) and Phase C (deterministic workflow) changes

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0002_rename_workflow_se_code_idx_workflow_se_code_ecae7f_idx_and_more'),
        ('catalog', '0001_initial'),
        ('templates', '0001_initial'),
    ]

    operations = [
        # PHASE B: Create ServiceVisitItem model
        migrations.CreateModel(
            name='ServiceVisitItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_name_snapshot', models.CharField(help_text='Service name at time of order', max_length=150)),
                ('department_snapshot', models.CharField(help_text='Department/category at time of order (USG/OPD/etc)', max_length=50)),
                ('price_snapshot', models.DecimalField(decimal_places=2, help_text='Price at time of order', max_digits=10)),
                ('status', models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('FINALIZED', 'Finalized'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], db_index=True, default='REGISTERED', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='service_visit_items', to='catalog.service')),
                ('service_visit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='workflow.servicevisit')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='servicevisititem',
            index=models.Index(fields=['service_visit'], name='workflow_se_service__idx'),
        ),
        migrations.AddIndex(
            model_name='servicevisititem',
            index=models.Index(fields=['service'], name='workflow_se_service_2_idx'),
        ),
        
        # PHASE C: Add timestamp fields to ServiceVisitItem
        migrations.AddField(
            model_name='servicevisititem',
            name='started_at',
            field=models.DateTimeField(blank=True, help_text='When item moved to IN_PROGRESS', null=True),
        ),
        migrations.AddField(
            model_name='servicevisititem',
            name='submitted_at',
            field=models.DateTimeField(blank=True, help_text='When item moved to PENDING_VERIFICATION', null=True),
        ),
        migrations.AddField(
            model_name='servicevisititem',
            name='verified_at',
            field=models.DateTimeField(blank=True, help_text='When item was verified', null=True),
        ),
        migrations.AddField(
            model_name='servicevisititem',
            name='published_at',
            field=models.DateTimeField(blank=True, help_text='When item was published', null=True),
        ),
        
        # PHASE B: Make ServiceVisit.service nullable
        migrations.AlterField(
            model_name='servicevisit',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='service_visits', to='workflow.servicecatalog'),
        ),
        
        # PHASE C: Make ServiceVisit.status editable=False
        migrations.AlterField(
            model_name='servicevisit',
            name='status',
            field=models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('FINALIZED', 'Finalized'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], db_index=True, default='REGISTERED', editable=False, help_text='DERIVED: Auto-calculated from ServiceVisitItem.status values', max_length=30),
        ),
        
        # PHASE C: Add service_visit_item FK to StatusAuditLog
        migrations.AddField(
            model_name='statusauditlog',
            name='service_visit_item',
            field=models.ForeignKey(blank=True, help_text='Item that transitioned (PHASE C: primary)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_audit_logs', to='workflow.servicevisititem'),
        ),
        
        # PHASE C: Make service_visit nullable in StatusAuditLog
        migrations.AlterField(
            model_name='statusauditlog',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Visit containing the item (for backward compatibility)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_audit_logs', to='workflow.servicevisit'),
        ),
        
        # PHASE B: Update Invoice model
        migrations.AddField(
            model_name='invoice',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Sum of line items before discount', max_digits=10),
        ),
        migrations.AddField(
            model_name='invoice',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Discount percentage (if applicable)', max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='receipt_number',
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=20, null=True, unique=True),
        ),
        
        # PHASE B: Update USGReport
        migrations.AddField(
            model_name='usgreport',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usg_report', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='usgreport',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usg_reports', to='workflow.servicevisit'),
        ),
        
        # PHASE C: Add template_version to USGReport
        migrations.AddField(
            model_name='usgreport',
            name='template_version',
            field=models.ForeignKey(blank=True, help_text='Template version used for this report (bridge to template system)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='templates.templateversion'),
        ),
        
        # PHASE B: Update OPDVitals
        migrations.AddField(
            model_name='opdvitals',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_vitals', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='opdvitals',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_vitals_list', to='workflow.servicevisit'),
        ),
        
        # PHASE B: Update OPDConsult
        migrations.AddField(
            model_name='opdconsult',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_consult', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='opdconsult',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_consults', to='workflow.servicevisit'),
        ),
    ]
