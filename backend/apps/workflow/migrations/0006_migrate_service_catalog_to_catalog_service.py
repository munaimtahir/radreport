from django.db import migrations


def migrate_service_catalog(apps, schema_editor):
    ServiceCatalog = apps.get_model("workflow", "ServiceCatalog")
    Service = apps.get_model("catalog", "Service")
    Modality = apps.get_model("catalog", "Modality")
    db_alias = schema_editor.connection.alias

    for legacy_service in ServiceCatalog.objects.using(db_alias).all():
        modality_code = (legacy_service.code or "").strip().upper() or "GENERAL"
        modality, _ = Modality.objects.using(db_alias).get_or_create(
            code=modality_code,
            defaults={"name": modality_code},
        )
        category = "OPD" if modality_code == "OPD" else "Radiology"

        Service.objects.using(db_alias).update_or_create(
            code=legacy_service.code,
            defaults={
                "modality": modality,
                "name": legacy_service.name,
                "category": category,
                "price": legacy_service.default_price,
                "charges": legacy_service.default_price,
                "default_price": legacy_service.default_price,
                "turnaround_time": legacy_service.turnaround_time,
                "is_active": legacy_service.is_active,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_service_default_price_turnaround_time"),
        ("workflow", "0005_phase_d_canonical_usg_report"),
    ]

    operations = [
        migrations.RunPython(migrate_service_catalog, migrations.RunPython.noop),
    ]
