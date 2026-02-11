from django.core.management.base import BaseCommand, CommandError

from apps.backups.services import BackupError, restore_backup


class Command(BaseCommand):
    help = "Restore backup by id or folder name"

    def add_arguments(self, parser):
        parser.add_argument("backup_id")
        parser.add_argument("--confirm-phrase", default="", required=False)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--yes", action="store_true")
        parser.add_argument("--allow-system-caddy-overwrite", action="store_true")
        parser.add_argument("--created-by", default="system")

    def handle(self, *args, **options):
        if not options["confirm_phrase"]:
            raise CommandError("--confirm-phrase is required and must be 'RESTORE NOW'")

        try:
            job = restore_backup(
                backup_id=options["backup_id"],
                created_by=options["created_by"],
                confirm_phrase=options["confirm_phrase"],
                dry_run=options["dry_run"],
                yes=options["yes"],
                allow_system_caddy_overwrite=options["allow_system_caddy_overwrite"],
            )
        except BackupError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Restore completed: {job.id}"))
