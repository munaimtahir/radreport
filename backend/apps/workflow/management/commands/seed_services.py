"""
Management command to seed catalog.Service with USG and OPD services.
"""
from django.core.management.base import BaseCommand
from apps.catalog.models import Modality, Service


class Command(BaseCommand):
    help = "Seed catalog.Service with USG and OPD services"

    def handle(self, *args, **options):
        services = [
            {
                'code': 'USG',
                'name': 'Ultrasound',
                'default_price': 2000.00,
                'turnaround_time': 60,  # 60 minutes
                'is_active': True,
            },
            {
                'code': 'OPD',
                'name': 'Outpatient Department Consultation',
                'default_price': 500.00,
                'turnaround_time': 30,  # 30 minutes
                'is_active': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for service_data in services:
            modality, _ = Modality.objects.get_or_create(
                code=service_data["code"],
                defaults={"name": service_data["code"]},
            )
            category = "OPD" if service_data["code"] == "OPD" else "Radiology"
            service, created = Service.objects.update_or_create(
                code=service_data["code"],
                defaults={
                    "modality": modality,
                    "name": service_data["name"],
                    "category": category,
                    "price": service_data["default_price"],
                    "charges": service_data["default_price"],
                    "default_price": service_data["default_price"],
                    "turnaround_time": service_data["turnaround_time"],
                    "is_active": service_data["is_active"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service.code} - {service.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated service: {service.code} - {service.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {created_count} created, {updated_count} updated'
            )
        )
