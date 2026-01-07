# Generated manually for patient_reg_no field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0002_patient_date_of_birth_alter_patient_mrn'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='patient_reg_no',
            field=models.CharField(blank=True, db_index=True, editable=False, help_text='Permanent patient registration number', max_length=30, null=True, unique=True),
        ),
        migrations.AddIndex(
            model_name='patient',
            index=models.Index(fields=['patient_reg_no'], name='patients_pa_patient_idx'),
        ),
    ]
