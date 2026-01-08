# Generated migration for Phase C: Deterministic Workflow Execution

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0002_phase_b_consolidation'),
        ('templates', '0001_initial'),
    ]

    operations = [
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
        
        # PHASE C: Add service_visit_item FK to StatusAuditLog (item-level tracking)
        migrations.AddField(
            model_name='statusauditlog',
            name='service_visit_item',
            field=models.ForeignKey(blank=True, help_text='Item that transitioned (PHASE C: primary)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_audit_logs', to='workflow.servicevisititem'),
        ),
        
        # PHASE C: Make service_visit nullable in StatusAuditLog (backward compatibility)
        migrations.AlterField(
            model_name='statusauditlog',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Visit containing the item (for backward compatibility)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='status_audit_logs', to='workflow.servicevisit'),
        ),
        
        # PHASE C: Add template_version FK to USGReport (template bridge)
        migrations.AddField(
            model_name='usgreport',
            name='template_version',
            field=models.ForeignKey(blank=True, help_text='Template version used for this report (bridge to template system)', null=True, on_delete=django.db.models.deletion.SET_NULL, to='templates.templateversion'),
        ),
        
        # PHASE C: Add help_text to ServiceVisit.status indicating it's derived
        migrations.AlterField(
            model_name='servicevisit',
            name='status',
            field=models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], db_index=True, default='REGISTERED', editable=False, help_text='DERIVED: Auto-calculated from ServiceVisitItem.status values', max_length=30),
        ),
    ]
