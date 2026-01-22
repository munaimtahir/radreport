"""
Management command to fix missing service snapshots in ServiceVisitItem records.

This fixes the issue where USG services appear in registration but not on receipts.

Usage:
    python manage.py fix_receipt_snapshots
    python manage.py fix_receipt_snapshots --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workflow.models import ServiceVisitItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix missing service snapshots (name, department, price) in ServiceVisitItem records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        if dry_run:
            self.stdout.write(self.style.WARNING('  Receipt Snapshot Fix (DRY RUN)'))
        else:
            self.stdout.write(self.style.WARNING('  Receipt Snapshot Fix'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # Find items with missing snapshots
        items = ServiceVisitItem.objects.filter(service__isnull=False)
        
        total = items.count()
        fixed_name = 0
        fixed_dept = 0
        fixed_price = 0
        errors = 0

        self.stdout.write(f'Checking {total} service visit items...')
        self.stdout.write('')

        for item in items:
            fixes_applied = []
            
            try:
                # Fix service_name_snapshot
                if not item.service_name_snapshot or item.service_name_snapshot.strip() == '':
                    if item.service:
                        if not dry_run:
                            item.service_name_snapshot = item.service.name
                        fixes_applied.append(f'name: "{item.service.name}"')
                        fixed_name += 1

                # Fix department_snapshot
                if not item.department_snapshot or item.department_snapshot.strip() == '':
                    if item.service:
                        dept = 'GENERAL'
                        if hasattr(item.service, 'modality') and item.service.modality:
                            dept = item.service.modality.code
                        elif hasattr(item.service, 'category') and item.service.category:
                            dept = item.service.category
                        
                        if not dry_run:
                            item.department_snapshot = dept
                        fixes_applied.append(f'dept: "{dept}"')
                        fixed_dept += 1

                # Fix price_snapshot
                if not item.price_snapshot or item.price_snapshot == Decimal('0'):
                    if item.service:
                        price = item.service.price if hasattr(item.service, 'price') else Decimal('0')
                        if not dry_run:
                            item.price_snapshot = price
                        fixes_applied.append(f'price: {price}')
                        fixed_price += 1

                # Save if any fixes applied
                if fixes_applied:
                    if not dry_run:
                        item.save()
                    
                    self.stdout.write(
                        f'  {"✓" if not dry_run else "→"} Item {str(item.id)[:8]}: {", ".join(fixes_applied)}'
                    )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Item {str(item.id)[:8]}: Error - {str(e)}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('  Summary'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(f'  Total items checked: {total}')
        self.stdout.write(self.style.SUCCESS(f'  Service names fixed: {fixed_name}'))
        self.stdout.write(self.style.SUCCESS(f'  Departments fixed: {fixed_dept}'))
        self.stdout.write(self.style.SUCCESS(f'  Prices fixed: {fixed_price}'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'  Errors: {errors}'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
            self.stdout.write('Run without --dry-run to apply fixes')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Snapshot fixes applied!'))
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('  1. Generate a new receipt to verify services show up')
            self.stdout.write('  2. Check receipt PDF includes all services')

        self.stdout.write('')

        # Verification
        if not dry_run and (fixed_name > 0 or fixed_dept > 0 or fixed_price > 0):
            self.stdout.write('Verification:')
            missing_name = ServiceVisitItem.objects.filter(
                service__isnull=False,
                service_name_snapshot=''
            ).count()
            missing_dept = ServiceVisitItem.objects.filter(
                service__isnull=False,
                department_snapshot=''
            ).count()
            missing_price = ServiceVisitItem.objects.filter(
                service__isnull=False,
                price_snapshot=Decimal('0')
            ).count()
            
            self.stdout.write(f'  Items still missing name: {missing_name}')
            self.stdout.write(f'  Items still missing dept: {missing_dept}')
            self.stdout.write(f'  Items still missing price: {missing_price}')
            
            if missing_name == 0 and missing_dept == 0 and missing_price == 0:
                self.stdout.write(self.style.SUCCESS('  ✓ All snapshots fixed!'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠ Some items still need fixing (may be missing service link)'))
            self.stdout.write('')
