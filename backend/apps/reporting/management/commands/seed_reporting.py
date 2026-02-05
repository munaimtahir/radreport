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
            defaults={
                "name": "USG KUB (Kidneys, Ureters, Bladder)", 
                "modality": "USG",
                "enable_narrative": True,
                "narrative_mode": "rule_based"
            }
        )
        
        if created:
            self.stdout.write(f"Created profile: {profile}")
            
            # Parameters
            params = [
                # Kidneys Section
                {
                    "section": "Kidneys", "name": "Right Kidney Size", "type": "short_text", "unit": "cm", "order": 1, "default": "Normal in size",
                    "sentence_template": "Right kidney size: {value}{unit}."
                },
                {
                    "section": "Kidneys", "name": "Left Kidney Size", "type": "short_text", "unit": "cm", "order": 2, "default": "Normal in size",
                     "sentence_template": "Left kidney size: {value}{unit}."
                },
                {
                    "section": "Kidneys", "name": "Right Kidney Echogenicity", "type": "dropdown", "order": 3, "options": ["Normal", "Increased", "Decreased"],
                     "sentence_template": "Right kidney echogenicity is {value}."
                },
                {
                    "section": "Kidneys", "name": "Left Kidney Echogenicity", "type": "dropdown", "order": 4, "options": ["Normal", "Increased", "Decreased"],
                     "sentence_template": "Left kidney echogenicity is {value}."
                },
                {
                    "section": "Kidneys", "name": "Cortico-medullary Differentiation", "type": "boolean", "order": 5, "default": "true",
                    "sentence_template": "Cortico-medullary differentiation is maintained."
                },
                {
                    "section": "Kidneys", "name": "Hydronephrosis", "type": "dropdown", "order": 6, "options": ["None", "Mild", "Moderate", "Severe"], "default": "None",
                    "sentence_template": "Hydronephrosis: {value}.",
                    "omit_if_values": ["None"]
                },
                {
                    "section": "Kidneys", "name": "Calculi/Masses", "type": "long_text", "order": 7, "default": "No calculus or mass lesion seen.",
                    "narrative_role": "finding"
                },

                # Urinary Bladder Section
                {
                    "section": "Urinary Bladder", "name": "Wall Thickness", "type": "number", "unit": "mm", "order": 10, "default": "3",
                    "sentence_template": "Bladder wall thickness is {value}{unit}."
                },
                {
                    "section": "Urinary Bladder", "name": "Lumen", "type": "short_text", "order": 11, "default": "Clear"
                },
                {
                    "section": "Urinary Bladder", "name": "Urinary bladder stone", "type": "boolean", "order": 12, "default": "false",
                     "sentence_template": "Urinary bladder stone seen."
                },
                {
                    "section": "Urinary Bladder", "name": "Pre-void Volume", "type": "number", "unit": "ml", "order": 13
                },
                
                # Prostrate (Males)
                {"section": "Prostate", "name": "Size", "type": "short_text", "order": 20, "default": "Normal"},
                {"section": "Prostate", "name": "Volume", "type": "number", "unit": "cc", "order": 21},
                
                # Impression Hints (User types, logic aggregates)
                {
                    "section": "Conclusion", "name": "Overall Impression", "type": "long_text", "order": 100, "default": "",
                    "narrative_role": "impression_hint",
                    "sentence_template": "{value}"
                },
                {
                    "section": "Conclusion", "name": "Specific Findings", "type": "checklist", "order": 101, 
                    "options": ["Renal Calculus", "Cystitis", "Prostatomegaly"],
                    "narrative_role": "impression_hint",
                    "join_label": " and ",
                    "sentence_template": "Features suggestive of {value}."
                }
            ]

            for p in params:
                param = ReportParameter.objects.create(
                    profile=profile,
                    section=p["section"],
                    name=p["name"],
                    parameter_type=p["type"],
                    unit=p.get("unit"),
                    normal_value=p.get("default"),
                    order=p["order"],
                    sentence_template=p.get("sentence_template"),
                    narrative_role=p.get("narrative_role", "finding"),
                    omit_if_values=p.get("omit_if_values"),
                    join_label=p.get("join_label")
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
             self.stdout.write(f"Profile {profile} already exists. Skipping seed to preserve manual changes.")

        # Link to a Service
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
