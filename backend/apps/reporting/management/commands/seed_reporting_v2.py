from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed V2 reporting templates + service mappings"

    def handle(self, *args, **options):
        call_command("import_templates_v2")
        self.stdout.write(self.style.SUCCESS("V2 reporting templates imported."))
