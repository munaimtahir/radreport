from django.core.management.base import BaseCommand

from apps.catalog.models import Modality, Service


class Command(BaseCommand):
    help = "Seed minimal USG services (Ultrasound Abdomen/Pelvis/KUB)."

    def handle(self, *args, **options):
        modality, _ = Modality.objects.get_or_create(
            code="USG",
            defaults={"name": "Ultrasound"}
        )

        services = [
            ("USG_ABDOMEN", "Ultrasound Abdomen"),
            ("USG_PELVIS", "Ultrasound Pelvis"),
            ("USG_KUB", "Ultrasound KUB"),
        ]

        for code, name in services:
            service, created = Service.objects.get_or_create(
                code=code,
                defaults={
                    "modality": modality,
                    "name": name,
                    "category": "Radiology",
                    "price": 0,
                    "charges": 0,
                    "default_price": 0,
                }
            )
            if not created:
                updated = False
                if service.modality_id != modality.id:
                    service.modality = modality
                    updated = True
                if service.name != name:
                    service.name = name
                    updated = True
                if service.category != "Radiology":
                    service.category = "Radiology"
                    updated = True
                if updated:
                    service.save()
                self.stdout.write(self.style.SUCCESS(f"Updated {service.code} -> {service.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Created {service.code} -> {service.name}"))
