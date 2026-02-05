from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reporting", "0013_reportblocklibrary"),
    ]

    operations = [
        migrations.DeleteModel(name="ReportActionLog"),
        migrations.DeleteModel(name="ReportInstance"),
        migrations.DeleteModel(name="ReportParameter"),
        migrations.DeleteModel(name="ReportParameterLibraryItem"),
        migrations.DeleteModel(name="ReportParameterOption"),
        migrations.DeleteModel(name="ReportProfile"),
        migrations.DeleteModel(name="ReportProfileParameterLink"),
        migrations.DeleteModel(name="ReportPublishSnapshot"),
        migrations.DeleteModel(name="ReportValue"),
        migrations.DeleteModel(name="ServiceReportProfile"),
        migrations.DeleteModel(name="TemplateAuditLog"),
    ]
