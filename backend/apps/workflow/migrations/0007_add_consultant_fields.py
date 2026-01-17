from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("consultants", "0001_initial"),
        ("workflow", "0006_migrate_service_catalog_to_catalog_service"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicevisit",
            name="booked_consultant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="booked_visits",
                to="consultants.consultantprofile",
            ),
        ),
        migrations.AddField(
            model_name="servicevisititem",
            name="consultant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="service_visit_items",
                to="consultants.consultantprofile",
            ),
        ),
    ]
