from django.core.management.base import BaseCommand

from apps.backups.services import apply_retention_policy


class Command(BaseCommand):
    help = "Apply backup retention policy: keep last 7 successful cron backups"

    def handle(self, *args, **options):
        deleted = apply_retention_policy()
        if deleted:
            self.stdout.write(self.style.WARNING(f"Deleted: {', '.join(deleted)}"))
        else:
            self.stdout.write(self.style.SUCCESS("No backups deleted by retention policy"))
