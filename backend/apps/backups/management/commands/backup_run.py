from django.core.management.base import BaseCommand, CommandError

from apps.backups.services import BackupError, create_backup_job


class Command(BaseCommand):
    help = "Run a full backup with metadata, checksums, and retention"

    def add_arguments(self, parser):
        parser.add_argument("--trigger", default="manual", choices=["cron", "manual", "api", "system"])
        parser.add_argument("--created-by", default="system")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--deletable", action="store_true")

    def handle(self, *args, **options):
        try:
            job = create_backup_job(
                created_by=options["created_by"],
                trigger=options["trigger"],
                deletable=options["deletable"],
                force=options["force"],
            )
        except BackupError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Backup completed: {job.id} -> {job.backup_path}"))
