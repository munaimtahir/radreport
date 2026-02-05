from django.core.management.base import BaseCommand
from apps.reporting.models import ReportProfile

class Command(BaseCommand):
    help = 'Create the USG_ABD report profile if it does not exist.'

    def handle(self, *args, **options):
        profile, created = ReportProfile.objects.update_or_create(
            code='USG_ABD',
            defaults={
                'name': 'Ultrasound Abdomen',
                'modality': 'USG',
                'is_active': True,
                'narrative_mode': 'rule_based'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created ReportProfile "USG_ABD"'))
        else:
            self.stdout.write(self.style.WARNING('ReportProfile "USG_ABD" already exists.'))
