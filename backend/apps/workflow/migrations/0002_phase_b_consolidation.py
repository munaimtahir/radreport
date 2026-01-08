# Generated migration for Phase B: Core Model Enforcement

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0001_initial'),
        ('catalog', '0001_initial'),
    ]

    operations = [
        # Add ServiceVisitItem model
        migrations.CreateModel(
            name='ServiceVisitItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('service_name_snapshot', models.CharField(help_text='Service name at time of order', max_length=150)),
                ('department_snapshot', models.CharField(help_text='Department/category at time of order (USG/OPD/etc)', max_length=50)),
                ('price_snapshot', models.DecimalField(decimal_places=2, help_text='Price at time of order', max_digits=10)),
                ('status', models.CharField(choices=[('REGISTERED', 'Registered'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification'), ('RETURNED_FOR_CORRECTION', 'Returned for Correction'), ('PUBLISHED', 'Published'), ('CANCELLED', 'Cancelled')], db_index=True, default='REGISTERED', max_length=30)),
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
        migrations.AddIndex(
            model_name='servicevisititem',
            index=models.Index(fields=['status'], name='workflow_se_status_idx'),
        ),
        
        # Make ServiceVisit.service nullable (for backward compatibility)
        migrations.AlterField(
            model_name='servicevisit',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='service_visits', to='workflow.servicecatalog'),
        ),
        
        # Update Invoice model - add new fields
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
        
        # Update USGReport - add service_visit_item field
        migrations.AddField(
            model_name='usgreport',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usg_report', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='usgreport',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usg_reports', to='workflow.servicevisit'),
        ),
        
        # Update OPDVitals - add service_visit_item field
        migrations.AddField(
            model_name='opdvitals',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_vitals', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='opdvitals',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_vitals_list', to='workflow.servicevisit'),
        ),
        
        # Update OPDConsult - add service_visit_item field
        migrations.AddField(
            model_name='opdconsult',
            name='service_visit_item',
            field=models.OneToOneField(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_consult', to='workflow.servicevisititem'),
        ),
        migrations.AlterField(
            model_name='opdconsult',
            name='service_visit',
            field=models.ForeignKey(blank=True, help_text='Legacy field - use service_visit_item instead', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='opd_consults', to='workflow.servicevisit'),
        ),
    ]
