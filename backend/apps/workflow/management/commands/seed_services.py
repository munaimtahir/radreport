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
            
            # Check for existing service by (modality, name) first to handle unique_together constraint
            try:
                existing_service = Service.objects.get(modality=modality, name=service_data["name"])
                # Update the existing service
                existing_service.code = service_data["code"]
                existing_service.category = category
                existing_service.price = service_data["default_price"]
                existing_service.charges = service_data["default_price"]
                existing_service.default_price = service_data["default_price"]
                existing_service.turnaround_time = service_data["turnaround_time"]
                existing_service.is_active = service_data["is_active"]
                existing_service.save()
                service = existing_service
                created = False
            except Service.DoesNotExist:
                # No existing service with this (modality, name), use update_or_create with code
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
