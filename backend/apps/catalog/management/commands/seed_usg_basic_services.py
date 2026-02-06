from django.core.management.base import BaseCommand

from apps.catalog.models import Modality, Service


class Command(BaseCommand):
    help = "Seed minimal USG core services (Abdomen/KUB/Pelvis)."

    def handle(self, *args, **options):
        modality, _ = Modality.objects.get_or_create(
            code="USG",
            defaults={"name": "Ultrasound"},
        )

        services = [
            ("USG-ABD", "USG Abdomen"),
            ("USG-KUB", "USG KUB"),
            ("USG-PELVIS", "USG Pelvis"),
        ]

        for code, name in services:
            _, created = Service.objects.update_or_create(
                code=code,
                defaults={
                    "modality": modality,
                    "name": name,
                    "category": "Radiology",
                    "price": 0,
                    "charges": 0,
                    "default_price": 0,
                },
            )
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} {code} -> {name}"))
