import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.reporting.models import ReportBlockLibrary


class _DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Import block library seeds (v1.x) into ReportBlockLibrary"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            dest="path",
            type=str,
            help="Directory containing block JSON seeds (default: phase2_v1.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate without persisting changes",
        )

    def handle(self, *args, **options):
        default_dir = Path(__file__).resolve().parents[2] / "seed_data" / "block_library" / "phase2_v1.1"
        seeds_dir = Path(options.get("path") or default_dir)
        dry_run = options.get("dry_run", False)

        if not seeds_dir.exists() or not seeds_dir.is_dir():
            raise CommandError(f"Seed directory not found: {seeds_dir}")

        self.stdout.write(self.style.MIGRATE_HEADING("Importing block library seeds"))
        self.stdout.write(f"Source: {seeds_dir}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no database writes"))

        stats = {"created": 0, "updated": 0, "unchanged": 0, "errors": []}

        try:
            with transaction.atomic():
                for path in sorted(seeds_dir.glob("*.json")):
                    self._import_file(path, stats)
                if dry_run:
                    raise _DryRunRollback()
        except _DryRunRollback:
            pass

        self._print_summary(stats)

    def _import_file(self, path: Path, stats: dict):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - unlikely
            stats["errors"].append(f"{path.name}: invalid JSON ({exc})")
            return

        code = payload.get("code") or payload.get("content", {}).get("code")
        name = payload.get("name")
        if not name:
            stats["errors"].append(f"{path.name}: missing name")
            return

        defaults = {
            "name": name,
            "category": payload.get("category", "USG"),
            "block_type": payload.get("block_type", "ui"),
            "content": payload.get("content", {}),
        }

        lookup = {"name": name}
        if code:
            lookup = {"content__code": code}

        obj, created = ReportBlockLibrary.objects.update_or_create(defaults=defaults, **lookup)
        if created:
            stats["created"] += 1
        else:
            if obj.name == name and obj.content == defaults["content"] and obj.category == defaults["category"] and obj.block_type == defaults["block_type"]:
                stats["unchanged"] += 1
            else:
                stats["updated"] += 1

    def _print_summary(self, stats: dict):
        self.stdout.write("\n--- Block Library Import Summary ---")
        self.stdout.write(f"Created:   {stats['created']}")
        self.stdout.write(f"Updated:   {stats['updated']}")
        self.stdout.write(f"Unchanged: {stats['unchanged']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors ({len(stats['errors'])}):"))
            for err in stats["errors"]:
                self.stdout.write(f" - {err}")
        self.stdout.write("------------------------------------")
