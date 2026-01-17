"""
Management command to import ultrasound services from CSV file
This command will delete all existing services and import new ones from the CSV
"""
import csv
from django.core.management.base import BaseCommand
from apps.catalog.models import Modality, Service
from apps.studies.models import OrderItem, Study


class Command(BaseCommand):
    help = "Import ultrasound services from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file containing services',
            default='/tmp/rims_services_ultrasound_import.csv'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Importing Ultrasound Services"))
        self.stdout.write("=" * 60)
        
        # Step 1: Delete all existing services and related objects
        self.stdout.write("\n[1/3] Deleting all existing services and related data...")
        
        # Delete OrderItems first (they reference services)
        order_items_deleted = OrderItem.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f"✓ Deleted {order_items_deleted} order items"))
        
        # Delete Studies next (they also reference services)
        studies_deleted = Study.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f"✓ Deleted {studies_deleted} studies"))
        
        # Now delete services
        deleted_count = Service.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f"✓ Deleted {deleted_count} existing services"))
        
        # Step 2: Ensure USG modality exists
        self.stdout.write("\n[2/3] Ensuring USG modality exists...")
        modality, created = Modality.objects.get_or_create(
            code="USG",
            defaults={"name": "Ultrasound"}
        )
        self.stdout.write(self.style.SUCCESS(
            f"✓ {'Created' if created else 'Exists'}: {modality.code} - {modality.name}"
        ))
        
        # Step 3: Import services from CSV
        self.stdout.write("\n[3/3] Importing services from CSV...")
        created_count = 0
        errors = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        # Skip empty rows
                        if not row.get('service_code', '').strip():
                            continue
                        
                        service_code = row['service_code'].strip()
                        name = row['name'].strip()
                        department = row['department'].strip()
                        billing_group = row.get('billing_group', '').strip()
                        sub_category = row.get('sub_category', '').strip()
                        price = float(row['price'].strip())
                        currency = row.get('currency', 'PKR').strip()
                        tat_min = int(row['tat_min'].strip())
                        unit = row.get('unit', 'service').strip()
                        is_active = int(row.get('is_active', '1').strip()) == 1
                        
                        # Calculate tat_value and tat_unit from tat_minutes
                        # Round to nearest hour for tat_value (since it's an integer)
                        if tat_min < 60:
                            tat_value = 1  # Round up to 1 hour
                            tat_unit = "hours"
                        elif tat_min < 1440:  # Less than 24 hours
                            # Round to nearest hour
                            tat_value = round(tat_min / 60) if tat_min % 60 >= 30 else tat_min // 60
                            if tat_value == 0:
                                tat_value = 1
                            tat_unit = "hours"
                        else:
                            tat_value = round(tat_min / 1440) if tat_min % 1440 >= 720 else tat_min // 1440
                            if tat_value == 0:
                                tat_value = 1
                            tat_unit = "days"
                        
                        # Create service with approximate tat_value/tat_unit
                        # The save() method will recalculate tat_minutes, so we'll override it after
                        service = Service.objects.create(
                            code=service_code,
                            modality=modality,
                            name=name,
                            category=department,
                            price=price,
                            charges=price,
                            tat_value=tat_value,
                            tat_unit=tat_unit,
                            is_active=is_active,
                        )
                        
                        # Override tat_minutes with exact value from CSV (bypassing save() recalculation)
                        Service.objects.filter(id=service.id).update(tat_minutes=tat_min)
                        
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"✓ Created: {service_code} - {name} (TAT: {tat_min} min, Price: {price})"
                        ))
                        
                    except Exception as e:
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(f"✗ {error_msg}"))
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"\nError: CSV file not found at {csv_path}"))
            self.stdout.write(self.style.WARNING("Please provide the correct path using --csv-path"))
            return
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Import completed!"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"  - Deleted: {deleted_count} services")
        self.stdout.write(f"  - Created: {created_count} services")
        if errors:
            self.stdout.write(self.style.WARNING(f"  - Errors: {len(errors)}"))
            for error in errors:
                self.stdout.write(f"    - {error}")
        self.stdout.write(f"\nTotal services in database: {Service.objects.count()}")
