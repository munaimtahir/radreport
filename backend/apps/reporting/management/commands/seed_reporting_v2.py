from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed V2 reporting block library, templates, and service mappings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate without persisting changes",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        cmd_options = {"dry_run": dry_run}

        self.stdout.write(self.style.MIGRATE_HEADING("Starting V2 Reporting Seed"))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE ENABLED"))

        # 1. Seed Block Library
        self.stdout.write("\n[1/3] Importing Block Library...")
        try:
            call_command("import_block_library", **cmd_options)
            self.stdout.write(self.style.SUCCESS("✓ Block library imported."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Block library import failed: {e}"))
            raise

        # 2. Seed Templates & Mappings
        self.stdout.write("\n[2/3] Importing Templates & Mappings...")
        try:
            call_command("import_templates_v2", **cmd_options)
            self.stdout.write(self.style.SUCCESS("✓ Templates & mappings imported."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Template import failed: {e}"))
            raise

        self.stdout.write(self.style.SUCCESS("\nAll V2 reporting seeds completed successfully."))
