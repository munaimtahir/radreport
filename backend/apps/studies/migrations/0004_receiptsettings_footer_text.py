from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("studies", "0003_receiptsequence_receiptsettings_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="receiptsettings",
            name="footer_text",
            field=models.CharField(default="Computer generated receipt", max_length=200),
        ),
    ]
