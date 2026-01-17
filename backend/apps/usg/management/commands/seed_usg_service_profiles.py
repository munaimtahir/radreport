from django.core.management.base import BaseCommand

from apps.usg.models import UsgServiceProfile, UsgTemplate


class Command(BaseCommand):
    help = "Seed USG service profiles for Abdomen, KUB, and Pelvis services."

    def handle(self, *args, **options):
        profiles = [
            {
                "service_code": "USG_ABDOMEN",
                "template_code": "USG_ABDOMEN_BASE",
                "hidden_sections": [],
                "forced_na_fields": [],
            },
            {
                "service_code": "USG_KUB",
                "template_code": "USG_ABDOMEN_BASE",
                "hidden_sections": [
                    "liver",
                    "gallbladder",
                    "biliary_tree",
                    "pancreas",
                    "spleen",
                    "vessels",
                    "lymph_nodes",
                ],
                "forced_na_fields": [],
            },
            {
                "service_code": "USG_PELVIS",
                "template_code": "USG_PELVIS_BASE",
                "hidden_sections": [],
                "forced_na_fields": [],
            },
        ]

        for profile in profiles:
            template = UsgTemplate.objects.filter(
                code=profile["template_code"]
            ).order_by("-version").first()
            if not template:
                self.stdout.write(
                    self.style.WARNING(
                        f"Template {profile['template_code']} not found; skipping {profile['service_code']}."
                    )
                )
                continue

            obj, created = UsgServiceProfile.objects.update_or_create(
                service_code=profile["service_code"],
                defaults={
                    "template": template,
                    "hidden_sections": profile["hidden_sections"],
                    "forced_na_fields": profile["forced_na_fields"],
                },
            )

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} service profile {obj.service_code} -> {template.code}"
                )
            )
