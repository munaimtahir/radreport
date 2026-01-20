from django.core.management.base import BaseCommand
from apps.usg.models import UsgTemplate, UsgServiceProfile
from apps.catalog.models import Service
import json

class Command(BaseCommand):
    help = 'Seed USG templates and service profiles'

    def handle(self, *args, **options):
        self.stdout.write("Seeding USG Templates...")

        # 1. Define Standard Templates
        templates = [
            {
                "code": "USG_ABDOMEN_V1",
                "name": "USG Abdomen (General)",
                "category": "abdomen",
                "schema_json": {
                    "templateKey": "USG_ABDOMEN_V1",
                    "title": "Ultrasound Abdomen",
                    "sections": [
                        {
                            "id": "liver",
                            "title": "Liver",
                            "naAllowed": True,
                            "fields": [
                                {"id":"size","label":"Size","type":"short_text","default":""},
                                {"id":"echotexture","label":"Echotexture","type":"short_text","default":""},
                                {"id":"lesions","label":"Focal lesions","type":"long_text","default":""},
                                {"id":"ihbr","label":"IHBR","type":"select","options":["Normal","Dilated"],"default":"Normal"}
                            ]
                        },
                        {
                            "id": "gallbladder",
                            "title": "Gallbladder & Biliary Tree",
                            "naAllowed": True,
                            "fields": [
                                {"id":"status","label":"Status","type":"select","options":["Distended","Contracted","Pos-cholecystectomy"],"default":"Distended"},
                                {"id":"calculi","label":"Calculi","type":"short_text","default":"None seen"},
                                {"id":"wall_thickness","label":"Wall Thickness","type":"short_text","default":"Normal"},
                                {"id":"cbd","label":"CBD","type":"short_text","default":""}
                            ]
                        },
                        {
                            "id": "pancreas",
                            "title": "Pancreas",
                            "naAllowed": True,
                            "fields": [
                                {"id":"visualization","label":"Visualization","type":"select","options":["Visualized","Obscured by gas"],"default":"Visualized"},
                                {"id":"size_texture","label":"Size & Texture","type":"short_text","default":"Normal"}
                            ]
                        },
                        {
                            "id": "spleen",
                            "title": "Spleen",
                            "naAllowed": True,
                            "fields": [
                                {"id":"size","label":"Size (cm)","type":"number","default":""},
                                {"id":"echotexture","label":"Echotexture","type":"short_text","default":"Normal"}
                            ]
                        },
                        {
                            "id": "kidneys",
                            "title": "Kidneys",
                            "naAllowed": True,
                            "fields": [
                                {"id":"right_size","label":"Right Kidney Size","type":"short_text","default":""},
                                {"id":"left_size","label":"Left Kidney Size","type":"short_text","default":""},
                                {"id":"pc_system","label":"Pelvicalyceal System","type":"short_text","default":"No hydronephrosis appearing."},
                                {"id":"calculi","label":"Calculi","type":"short_text","default":"None seen"}
                            ]
                        },
                        {
                            "id": "bladder_prostate",
                            "title": "Urinary Bladder & Prostate",
                            "naAllowed": True,
                            "fields": [
                                {"id":"bladder_wall","label":"Bladder Wall","type":"short_text","default":"Normal"},
                                {"id":"prostate_vol","label":"Prostate Vol (approx)","type":"short_text","default":""}
                            ]
                        },
                        {
                            "id": "impression",
                            "title": "Impression",
                            "naAllowed": False,
                            "fields": [
                                {"id":"summary","label":"Summary","type":"long_text","default":""}
                            ]
                        }
                    ],
                    "impression": {"enabled": True},
                    "notes": {"enabled": True}
                }
            },
            {
                "code": "USG_PELVIS_V1",
                "name": "USG Pelvis (General)",
                "category": "pelvis",
                "schema_json": {
                    "templateKey": "USG_PELVIS_V1",
                    "title": "Ultrasound Pelvis",
                    "sections": [
                        {
                            "id": "bladder",
                            "title": "Urinary Bladder",
                            "naAllowed": True,
                            "fields": [
                                {"id":"filling","label":"Filling","type":"select","options":["Well filled","Partially filled"],"default":"Well filled"},
                                {"id":"wall","label":"Wall Thickness","type":"short_text","default":"Normal"},
                                {"id":"contents","label":"Intraluminal Contents","type":"short_text","default":"Clear"}
                            ]
                        },
                        {
                            "id": "uterus",
                            "title": "Uterus",
                            "naAllowed": True,
                            "fields": [
                                {"id":"size","label":"Size","type":"short_text","default":"Normal"},
                                {"id":"endometrium","label":"Endometrium","type":"short_text","default":""},
                                {"id":"mymetrium","label":"Myometrium","type":"short_text","default":"Homogeneous"}
                            ]
                        },
                        {
                            "id": "ovaries",
                            "title": "Ovaries / Adnexa",
                            "naAllowed": True,
                            "fields": [
                                {"id":"right_ovary","label":"Right Ovary","type":"short_text","default":"Normal"},
                                {"id":"left_ovary","label":"Left Ovary","type":"short_text","default":"Normal"},
                                {"id":"fluid","label":"Free Fluid","type":"short_text","default":"None seen"}
                            ]
                        },
                        {
                            "id": "prostate",
                            "title": "Prostate (Male)",
                            "naAllowed": True,
                            "fields": [
                                {"id":"size","label":"Size","type":"short_text","default":"Normal"},
                                {"id":"volume","label":"Volume (cc)","type":"number","default":""}
                            ]
                        },
                        {
                            "id": "impression",
                            "title": "Impression",
                            "naAllowed": False,
                            "fields": [
                                {"id":"summary","label":"Summary","type":"long_text","default":""}
                            ]
                        }
                    ]
                }
            }
        ]

        for t_data in templates:
            obj, created = UsgTemplate.objects.update_or_create(
                code=t_data["code"],
                defaults={
                    "name": t_data["name"],
                    "category": t_data["category"],
                    "schema_json": t_data["schema_json"],
                    "version": 1,
                    "is_locked": True
                }
            )
            self.stdout.write(f"Template {obj.code} {'created' if created else 'updated'}")

        # 2. Map Services
        # Find services containing strings
        mappings = [
            {"search": "USG Abdomen", "template_code": "USG_ABDOMEN_V1"},
            {"search": "USG Pelvis", "template_code": "USG_PELVIS_V1"},
        ]

        for mapping in mappings:
            # Case insensitive search
            services = Service.objects.filter(name__icontains=mapping["search"])
            if not services.exists():
                self.stdout.write(self.style.WARNING(f"No service found matching '{mapping['search']}'"))
                continue

            template = UsgTemplate.objects.get(code=mapping["template_code"])

            for service in services:
                # Ensure service has a unique code if missing, but Service.code is CSV driven.
                # UsgServiceProfile links by service_code. 
                # Ensure User knows service MUST have a code if using Profile.
                if not service.code:
                    self.stdout.write(self.style.WARNING(f"Service '{service.name}' has no code. Skipping mapping."))
                    continue

                profile, created = UsgServiceProfile.objects.update_or_create(
                    service_code=service.code,
                    defaults={
                        "template": template
                    }
                )
                self.stdout.write(f"Mapped Service '{service.name}' ({service.code}) -> {template.code} {'(created)' if created else '(updated)'}")

        self.stdout.write(self.style.SUCCESS("Seed complete."))
