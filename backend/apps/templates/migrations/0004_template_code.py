from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0003_add_audit_fields_to_report_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='code',
            field=models.CharField(blank=True, help_text='Unique identifier for template family', max_length=100, null=True, unique=True),
        ),
    ]
