from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_service_category_service_charges_service_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="default_price",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Legacy price alias",
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="service",
            name="turnaround_time",
            field=models.PositiveIntegerField(
                default=60,
                help_text="Legacy turnaround time in minutes",
            ),
        ),
    ]
