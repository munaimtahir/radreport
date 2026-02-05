from django.core.management.base import BaseCommand
from apps.catalog.models import Service, Modality

class Command(BaseCommand):
    help = "Seeds basic USG services (Phase 3 Core)"

    def handle(self, *args, **options):
        # Ensure Modality USG exists
        modality, _ = Modality.objects.get_or_create(code="USG", defaults={"name": "Ultrasound"})

        services = [
            {"code": "USG-ABD", "name": "USG Abdomen"},
            {"code": "USG-KUB", "name": "USG KUB"},
            {"code": "USG-PELVIS", "name": "USG Pelvis"},
        ]

        created_count = 0
        updated_count = 0

        for s in services:
            obj, created = Service.objects.update_or_create(
                code=s["code"],
                defaults={
                    "name": s["name"],
                    "modality": modality,
                    "is_active": True
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded USG Services: {created_count} created, {updated_count} updated."))
