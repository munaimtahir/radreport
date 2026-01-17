"""
Management command to update USG services with finalized list and charges.
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.catalog.models import Modality, Service
from apps.workflow.models import ServiceVisitItem


class Command(BaseCommand):
    help = "Update USG services with finalized list and charges"

    # Service definitions organized by category
    USG_SERVICES = {
        "Routine": [
            ("USG Abdomen", 1500),
            ("USG Abdomen & Pelvis", 3000),
            ("USG KUB", 1500),
            ("USG Pelvis", 1500),
            ("USG Soft Tissue", 2500),
            ("USG Swelling", 2500),
            ("USG Breast", 2500),
            ("USG Chest", 2500),
            ("USG Scrotum", 1500),
            ("USG Knee Joint", 2500),
            ("USG Hip Joints (Child)", 3000),
            ("USG Cranial", 2500),
        ],
        "Obstetric": [
            ("USG Obstetrics – Single (1st & 2nd Trimester)", 2000),
            ("USG Obstetrics – Twin", 3000),
            ("USG Obstetrics – Triplet", 9000),
            ("USG Anomaly / Congenital Scan", 4000),
        ],
        "Doppler": [
            ("Doppler Abdomen", 5000),
            ("Doppler Renal", 3500),
            ("Doppler Thyroid", 3500),
            ("Doppler Neck", 3500),
            ("Doppler Uterine", 3500),
            ("Doppler Peripheral Veins – Single Side", 3500),
            ("Doppler Peripheral Veins – Both Sides", 7500),
            ("Doppler Peripheral Arteries – Single Side", 3500),
            ("Doppler Peripheral Arteries – Both Sides", 7000),
            ("Doppler Peripheral Arteries & Veins – Both Sides", 7000),
            ("Doppler Scrotum", 3500),
        ],
        "USG-Guided Procedures": [
            ("USG-Guided Abscess Aspiration (Diagnostic)", 3000),
            ("USG-Guided Abscess Drainage (Therapeutic)", 5000),
            ("USG-Guided Ascitic Fluid Tap (Diagnostic)", 3000),
            ("USG-Guided Ascitic Fluid Tap (Therapeutic)", 5000),
            ("USG-Guided Pleural Effusion Tap (Diagnostic)", 2500),
            ("USG-Guided Pleural Effusion Tap (Therapeutic)", 5000),
        ],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        # Statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'naming_conflicts': [],
            'services_with_visits': [],
        }

        # Ensure USG modality exists
        modality, created = Modality.objects.get_or_create(
            code="USG",
            defaults={"name": "Ultrasound"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created modality: {modality.code} - {modality.name}'))
        else:
            self.stdout.write(f'Modality exists: {modality.code} - {modality.name}')

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('Processing USG Services')
        self.stdout.write('=' * 80 + '\n')

        # Process each category
        for category, services in self.USG_SERVICES.items():
            self.stdout.write(f'\n[{category} USG]')
            self.stdout.write('-' * 80)
            
            for service_name, charge in services:
                result = self._process_service(
                    modality=modality,
                    name=service_name,
                    charge=charge,
                    category=category,
                    dry_run=dry_run,
                    stats=stats
                )
                
                if result['action'] == 'created':
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {service_name} - {charge}")
                    )
                elif result['action'] == 'updated':
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {service_name} - {charge}")
                    )
                elif result['action'] == 'skipped':
                    self.stdout.write(
                        self.style.ERROR(f"  ⊘ Skipped: {service_name} - {result['reason']}")
                    )

        # Generate verification report
        self._print_verification_report(stats, dry_run)

    def _find_existing_service(self, modality, name):
        """
        Find existing service by exact name or similar name (handling em dash variations).
        Returns (service, normalized_name) tuple.
        """
        # Try exact match first
        exact_match = Service.objects.filter(
            modality=modality,
            name=name
        ).first()
        if exact_match:
            return exact_match, name
        
        # Try with em dash replaced by hyphen
        normalized_name = name.replace('–', '-')
        normalized_match = Service.objects.filter(
            modality=modality,
            name=normalized_name
        ).first()
        if normalized_match:
            return normalized_match, normalized_name
        
        # Try with hyphen replaced by em dash
        em_dash_name = name.replace('-', '–')
        em_dash_match = Service.objects.filter(
            modality=modality,
            name=em_dash_name
        ).first()
        if em_dash_match:
            return em_dash_match, em_dash_name
        
        # Try case-insensitive match
        case_insensitive = Service.objects.filter(
            modality=modality,
            name__iexact=name
        ).first()
        if case_insensitive:
            return case_insensitive, case_insensitive.name
        
        # No match found - use the provided name as-is
        return None, name

    def _process_service(self, modality, name, charge, category, dry_run, stats):
        """
        Process a single service: create or update with safety checks.
        Returns dict with action, reason, and service info.
        """
        # Generate service code based on category and name
        service_code = self._generate_service_code(name, category)
        
        # Find existing service (handles name variations)
        existing_by_name, final_name = self._find_existing_service(modality, name)
        
        # Use the final name (may be normalized if existing service found)
        # But prefer the provided name if no existing service
        if existing_by_name:
            # Use existing service's name to avoid breaking references
            final_name = existing_by_name.name
        else:
            # Use provided name as-is (preserves em dashes)
            final_name = name
        
        # Check for existing service by code
        existing_by_code = None
        if service_code:
            existing_by_code = Service.objects.filter(code=service_code).first()
        
        # Check if service has any visits (ServiceVisitItems)
        has_visits = False
        visit_count = 0
        if existing_by_name:
            visit_count = ServiceVisitItem.objects.filter(service=existing_by_name).count()
            has_visits = visit_count > 0
        
        # Decision logic
        if existing_by_name:
            # Service exists with this name (or similar)
            if has_visits:
                # Don't rename services with visits - only update charge if different
                if not dry_run and existing_by_name.charges != Decimal(str(charge)):
                    existing_by_name.charges = Decimal(str(charge))
                    existing_by_name.price = Decimal(str(charge))
                    existing_by_name.is_active = True
                    existing_by_name.save()
                    stats['updated'] += 1
                    return {'action': 'updated', 'service': existing_by_name}
                else:
                    stats['services_with_visits'].append({
                        'name': final_name,
                        'current_charge': float(existing_by_name.charges),
                        'new_charge': charge,
                        'visits': visit_count
                    })
                    stats['skipped'] += 1
                    return {'action': 'skipped', 'reason': f'Has {visit_count} visit(s), charge updated if different'}
            else:
                # No visits - safe to update name and other fields
                if not dry_run:
                    # Only update name if it's different (normalize if needed, but don't break references)
                    if existing_by_name.name != final_name:
                        # Check if the new name would conflict
                        conflict_check = Service.objects.filter(
                            modality=modality,
                            name=final_name
                        ).exclude(pk=existing_by_name.pk).first()
                        if not conflict_check:
                            existing_by_name.name = final_name
                    
                    existing_by_name.charges = Decimal(str(charge))
                    existing_by_name.price = Decimal(str(charge))
                    existing_by_name.is_active = True
                    existing_by_name.modality = modality
                    existing_by_name.category = "Radiology"
                    # Update code if not conflicting
                    if service_code and (not existing_by_code or existing_by_code.id == existing_by_name.id):
                        existing_by_name.code = service_code
                    existing_by_name.save()
                    stats['updated'] += 1
                    return {'action': 'updated', 'service': existing_by_name}
                else:
                    stats['updated'] += 1
                    return {'action': 'updated', 'service': existing_by_name}
        else:
            # New service - check for code conflict
            if existing_by_code and existing_by_code.name != final_name:
                stats['naming_conflicts'].append({
                    'name': final_name,
                    'code': service_code,
                    'conflicting_service': existing_by_code.name
                })
                # Still create, but with different code
                service_code = self._generate_service_code(name, category, suffix=True)
            
            # Create new service with exact name as provided
            if not dry_run:
                service = Service.objects.create(
                    code=service_code,
                    modality=modality,
                    name=final_name,  # Use provided name (preserves em dashes)
                    category="Radiology",
                    charges=Decimal(str(charge)),
                    price=Decimal(str(charge)),
                    default_price=Decimal(str(charge)),
                    is_active=True,
                    requires_radiologist_approval=True,
                    tat_value=1,
                    tat_unit="hours",
                )
                stats['created'] += 1
                return {'action': 'created', 'service': service}
            else:
                stats['created'] += 1
                return {'action': 'created', 'service': None}

    def _generate_service_code(self, name, category, suffix=False):
        """
        Generate a service code from name and category.
        Format: USG-{CATEGORY_PREFIX}-{NAME_SLUG}
        Max length: 50 characters (database constraint)
        """
        # Category prefixes (shorter versions to save space)
        category_map = {
            "Routine": "R",
            "Obstetric": "OB",
            "Doppler": "D",
            "USG-Guided Procedures": "G",
        }
        
        prefix = category_map.get(category, "USG")
        
        # Create slug from name
        slug = name.upper()
        # Replace em dashes with hyphens
        slug = slug.replace('–', '-')
        # Remove special characters, keep alphanumeric, spaces, and hyphens
        slug = ''.join(c if c.isalnum() or c in (' ', '-') else '' for c in slug)
        # Replace spaces with hyphens
        slug = slug.replace(' ', '-')
        # Remove multiple consecutive hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Calculate available length: "USG-{prefix}-{slug}" format
        # Reserve space for prefix, separators, and optional suffix
        prefix_part = f"USG-{prefix}-"
        max_slug_length = 50 - len(prefix_part) - (7 if suffix else 0)  # Reserve 7 for timestamp suffix
        
        # Truncate slug if needed
        if len(slug) > max_slug_length:
            slug = slug[:max_slug_length].rstrip('-')
        
        code = f"{prefix_part}{slug}"
        
        if suffix:
            # Add timestamp suffix for uniqueness (format: -HHMMSS)
            from datetime import datetime
            timestamp = datetime.now().strftime('%H%M%S')
            # Truncate code if needed to fit timestamp
            max_base_length = 50 - len(timestamp) - 1  # -1 for the hyphen
            if len(code) > max_base_length:
                code = code[:max_base_length].rstrip('-')
            code = f"{code}-{timestamp}"
        
        # Final safety check - ensure it's within 50 chars
        if len(code) > 50:
            code = code[:50].rstrip('-')
        
        return code

    def _print_verification_report(self, stats, dry_run):
        """Print verification report summary."""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('VERIFICATION REPORT')
        self.stdout.write('=' * 80 + '\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes were made\n'))
        
        self.stdout.write(f"Total Services Processed: {stats['created'] + stats['updated'] + stats['skipped']}")
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {stats['created']}"))
        self.stdout.write(self.style.WARNING(f"  ↻ Updated: {stats['updated']}"))
        self.stdout.write(self.style.ERROR(f"  ⊘ Skipped: {stats['skipped']}"))
        
        if stats['naming_conflicts']:
            self.stdout.write('\n' + self.style.WARNING('Naming Conflicts Resolved:'))
            for conflict in stats['naming_conflicts']:
                self.stdout.write(
                    f"  - {conflict['name']}: Code conflict with '{conflict['conflicting_service']}' "
                    f"(resolved with unique code)"
                )
        
        if stats['services_with_visits']:
            self.stdout.write('\n' + self.style.WARNING('Services with Existing Visits (charge updated only):'))
            for svc in stats['services_with_visits']:
                self.stdout.write(
                    f"  - {svc['name']}: {svc['visits']} visit(s), "
                    f"charge: {svc['current_charge']} → {svc['new_charge']}"
                )
        
        # Verify all services are active and have correct modality
        if not dry_run:
            usg_services = Service.objects.filter(modality__code="USG")
            inactive = usg_services.filter(is_active=False)
            wrong_modality = Service.objects.exclude(modality__code="USG").filter(
                name__icontains="USG"
            ).exclude(name__icontains="DOPPLER").exclude(name__icontains="GUIDED")
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('POST-UPDATE VERIFICATION')
            self.stdout.write('=' * 80)
            self.stdout.write(f"Total USG services: {usg_services.count()}")
            
            if inactive.exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ Inactive USG services: {inactive.count()}"))
                for svc in inactive[:5]:
                    self.stdout.write(f"    - {svc.name}")
            else:
                self.stdout.write(self.style.SUCCESS("  ✓ All USG services are active"))
            
            if wrong_modality.exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ Services with 'USG' in name but wrong modality: {wrong_modality.count()}"))
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ Update completed!'))
        self.stdout.write('=' * 80 + '\n')
