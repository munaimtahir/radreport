"""
Management command to verify USG template resolution.
Tests all possible failure points in the backend.

Usage:
    python manage.py verify_usg_template_resolution
    python manage.py verify_usg_template_resolution --report-id <uuid>
"""
from django.core.management.base import BaseCommand
from apps.workflow.models import USGReport
from apps.workflow.template_resolution import resolve_template_schema_for_report, ensure_template_for_report
from apps.catalog.models import Service as CatalogService
from rest_framework.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Verify USG template resolution for reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-id',
            type=str,
            help='Specific report ID to test',
        )

    def handle(self, *args, **options):
        report_id = options.get('report_id')
        
        if report_id:
            self.test_specific_report(report_id)
        else:
            self.test_all_reports()
    
    def test_specific_report(self, report_id):
        """Test a specific report by ID"""
        self.stdout.write("=" * 80)
        self.stdout.write(f"Testing Report: {report_id}")
        self.stdout.write("=" * 80)
        
        try:
            report = USGReport.objects.get(id=report_id)
            self.stdout.write(f"Status: {report.report_status}")
            self.stdout.write(f"Template Version: {report.template_version}")
            
            # Get service info
            service = None
            if report.service_visit_item and report.service_visit_item.service:
                service = report.service_visit_item.service
            elif report.service_visit and report.service_visit.service:
                service = report.service_visit.service
            
            if service:
                self.stdout.write(f"Service: {service.code}")
                self.stdout.write(f"Default Template: {service.default_template}")
            
            # Try to resolve
            schema = resolve_template_schema_for_report(report)
            sections = schema.get('sections', [])
            
            self.stdout.write(self.style.SUCCESS(f"✅ Schema resolved"))
            self.stdout.write(f"   Sections: {len(sections)}")
            
            if sections:
                self.stdout.write(f"   First section: {sections[0].get('title', 'N/A')}")
                fields = sections[0].get('fields', [])
                self.stdout.write(f"   Fields in first section: {len(fields)}")
                
                if fields:
                    self.stdout.write("\n   Sample fields:")
                    for i, field in enumerate(fields[:3]):
                        self.stdout.write(f"     {i+1}. {field.get('label', 'N/A')} ({field.get('type', 'N/A')})")
                        if field.get('options'):
                            self.stdout.write(f"        Options: {len(field['options'])} items")
                            
        except USGReport.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Report {report_id} not found"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"❌ Validation Error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {type(e).__name__}: {str(e)}"))
    
    def test_all_reports(self):
        """Test template resolution for all reports"""
        self.stdout.write("=" * 80)
        self.stdout.write("PHASE 5: Backend Template Resolution Verification")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # Statistics
        total_reports = USGReport.objects.count()
        self.stdout.write(f"📊 Total USG Reports: {total_reports}")
        
        if total_reports == 0:
            self.stdout.write(self.style.WARNING("⚠️  No USG reports found."))
            return
        
        reports_with_template = USGReport.objects.filter(template_version__isnull=False).count()
        reports_without_template = USGReport.objects.filter(template_version__isnull=True).count()
        
        self.stdout.write(f"✅ Reports WITH template_version: {reports_with_template}")
        self.stdout.write(f"❌ Reports WITHOUT template_version: {reports_without_template}")
        self.stdout.write("")
        
        # Test first report
        self.stdout.write("-" * 80)
        self.stdout.write("Testing first report:")
        self.stdout.write("-" * 80)
        
        report = USGReport.objects.first()
        self.stdout.write(f"Report ID: {report.id}")
        self.stdout.write(f"Status: {report.report_status}")
        self.stdout.write(f"Template Version: {report.template_version}")
        
        # Service info
        service = None
        if report.service_visit_item and report.service_visit_item.service:
            service = report.service_visit_item.service
        elif report.service_visit and report.service_visit.service:
            service = report.service_visit.service
        
        if service:
            self.stdout.write(f"Service: {service.code}")
            self.stdout.write(f"Default Template: {service.default_template}")
            
            if service.default_template:
                template = service.default_template
                versions = template.versions.filter(is_published=True).order_by("-version")
                self.stdout.write(f"Published Versions: {versions.count()}")
                
                if versions.exists():
                    latest = versions.first()
                    self.stdout.write(f"Latest Version: {latest.version}")
                    self.stdout.write(f"Schema exists: {bool(latest.schema)}")
                    if latest.schema:
                        sections = latest.schema.get('sections', [])
                        self.stdout.write(f"Schema sections: {len(sections)}")
        else:
            self.stdout.write(self.style.WARNING("❌ No service association!"))
        
        self.stdout.write("")
        
        # Try resolution
        self.stdout.write("-" * 80)
        self.stdout.write("Attempting to resolve template schema:")
        self.stdout.write("-" * 80)
        
        try:
            schema = resolve_template_schema_for_report(report)
            sections = schema.get('sections', [])
            self.stdout.write(self.style.SUCCESS(f"✅ SUCCESS: Schema resolved"))
            self.stdout.write(f"   Sections: {len(sections)}")
            
            if sections:
                self.stdout.write(f"   First section: {sections[0].get('title', 'N/A')}")
                fields = sections[0].get('fields', [])
                self.stdout.write(f"   Fields: {len(fields)}")
                
                if fields:
                    field = fields[0]
                    self.stdout.write(f"   Sample field: {field.get('label', 'N/A')} (type: {field.get('type', 'N/A')})")
                    
                    # Check for checklist/dropdown fields
                    checklist_fields = [f for f in fields if f.get('type') in ['checklist', 'multi_choice']]
                    dropdown_fields = [f for f in fields if f.get('type') == 'dropdown']
                    
                    self.stdout.write(f"   Checklist fields: {len(checklist_fields)}")
                    self.stdout.write(f"   Dropdown fields: {len(dropdown_fields)}")
                    
                    if checklist_fields:
                        sample = checklist_fields[0]
                        self.stdout.write(f"\n   Sample checklist field:")
                        self.stdout.write(f"     Label: {sample.get('label', 'N/A')}")
                        self.stdout.write(f"     Key: {sample.get('field_key') or sample.get('key')}")
                        self.stdout.write(f"     Options: {len(sample.get('options', []))} items")
                        if sample.get('options'):
                            opt = sample['options'][0]
                            self.stdout.write(f"     First option type: {type(opt).__name__}")
                            self.stdout.write(f"     First option: {opt}")
                        
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"❌ FAILED: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ERROR: {type(e).__name__}: {str(e)}"))
        
        self.stdout.write("")
        
        # Check USG services
        self.stdout.write("-" * 80)
        self.stdout.write("Checking USG services configuration:")
        self.stdout.write("-" * 80)
        
        usg_services = CatalogService.objects.filter(
            category="Radiology",
            modality__code="USG",
            is_active=True
        )
        
        self.stdout.write(f"Active USG Services: {usg_services.count()}")
        
        for svc in usg_services:
            has_template = "✅" if svc.default_template else "❌"
            template_name = svc.default_template.name if svc.default_template else "NONE"
            self.stdout.write(f"{has_template} {svc.code:30s} | {template_name}")
        
        self.stdout.write("")
        
        # Test draft report
        self.stdout.write("-" * 80)
        self.stdout.write("Testing ensure_template_for_report (publish/finalize):")
        self.stdout.write("-" * 80)
        
        draft_report = USGReport.objects.filter(report_status="DRAFT").first()
        
        if draft_report:
            self.stdout.write(f"Draft Report: {draft_report.id}")
            self.stdout.write(f"Current template_version: {draft_report.template_version}")
            
            try:
                template_version = ensure_template_for_report(draft_report)
                self.stdout.write(self.style.SUCCESS(f"✅ SUCCESS: Template ensured"))
                self.stdout.write(f"   Version: {template_version.version}")
                self.stdout.write(f"   Template: {template_version.template.name}")
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"❌ FAILED: {str(e)}"))
                self.stdout.write(self.style.ERROR("   This report would fail on publish/finalize!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ ERROR: {type(e).__name__}: {str(e)}"))
        else:
            self.stdout.write(self.style.WARNING("ℹ️  No DRAFT reports found"))
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("Verification Complete"))
        self.stdout.write("=" * 80)
