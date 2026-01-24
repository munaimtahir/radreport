from django.core.management.base import BaseCommand
from apps.reporting.models import ReportProfile, ReportParameter, ReportParameterOption, ServiceReportProfile
from apps.catalog.models import Service

class Command(BaseCommand):
    help = 'Seeds initial reporting profiles'

    def handle(self, *args, **options):
        self.stdout.write("Seeding reporting profiles...")
        
        # 1. USG KUB
        profile, created = ReportProfile.objects.get_or_create(
            code="USG_KUB",
            defaults={"name": "USG KUB (Kidneys, Ureters, Bladder)", "modality": "USG"}
        )
        
        if created:
            self.stdout.write(f"Created profile: {profile}")
            
            # Parameters
            params = [
                # Kidneys Section
                {"section": "Kidneys", "name": "Right Kidney Size", "type": "short_text", "unit": "cm", "order": 1, "default": "Normal in size"},
                {"section": "Kidneys", "name": "Left Kidney Size", "type": "short_text", "unit": "cm", "order": 2, "default": "Normal in size"},
                {"section": "Kidneys", "name": "Right Kidney Echogenicity", "type": "dropdown", "order": 3, "options": ["Normal", "Increased", "Decreased"]},
                {"section": "Kidneys", "name": "Left Kidney Echogenicity", "type": "dropdown", "order": 4, "options": ["Normal", "Increased", "Decreased"]},
                {"section": "Kidneys", "name": "Cortico-medullary Differentiation", "type": "boolean", "order": 5, "default": "true"},
                {"section": "Kidneys", "name": "Calculi/Masses", "type": "long_text", "order": 6, "default": "No calculus or mass lesion seen."},

                # Urinary Bladder Section
                {"section": "Urinary Bladder", "name": "Wall Thickness", "type": "number", "unit": "mm", "order": 10, "default": "3"},
                {"section": "Urinary Bladder", "name": "Lumen", "type": "short_text", "order": 11, "default": "Clear"},
                {"section": "Urinary Bladder", "name": "Pre-void Volume", "type": "number", "unit": "ml", "order": 12},
                
                # Prostrate (Males)
                {"section": "Prostate", "name": "Size", "type": "short_text", "order": 20, "default": "Normal"},
                {"section": "Prostate", "name": "Volume", "type": "number", "unit": "cc", "order": 21},
                
                # Impression
                {"section": "Conclusion", "name": "Impression", "type": "long_text", "order": 100, "default": "Normal study."}
            ]

            for p in params:
                param = ReportParameter.objects.create(
                    profile=profile,
                    section=p["section"],
                    name=p["name"],
                    parameter_type=p["type"],
                    unit=p.get("unit"),
                    normal_value=p.get("default"),
                    order=p["order"]
                )
                if "options" in p:
                    for i, opt in enumerate(p["options"]):
                        ReportParameterOption.objects.create(
                            parameter=param,
                            label=opt,
                            value=opt,
                            order=i
                        )
        else:
             self.stdout.write(f"Profile {profile} already exists.")

        # Link to a Service
        # Try to find a service named "USG KUB" or similar
        services = Service.objects.filter(name__icontains="KUB")
        if services.exists():
            for svc in services:
                ServiceReportProfile.objects.get_or_create(
                    service=svc,
                    profile=profile,
                    defaults={"enforce_single_profile": True}
                )
                self.stdout.write(f"Linked profile to service: {svc.name}")
        else:
            self.stdout.write("No matching KUB service found to link.")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
