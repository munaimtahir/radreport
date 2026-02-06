import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.reporting.models import ReportBlockLibrary


class _DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Import Phase-2 v1.1 block library seed JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="Path to a block-library seed JSON file or directory",
        )
        parser.add_argument("--dry-run", action="store_true", help="Validate without persisting")

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[2] / "seed_data" / "block_library" / "phase2_v1.1"
        path = Path(options.get("path") or base_dir)
        dry_run = options["dry_run"]

        stats = {"created": 0, "updated": 0}

        try:
            with transaction.atomic():
                for file_path in self._seed_files(path):
                    payload = json.loads(file_path.read_text(encoding="utf-8"))
                    rows = payload if isinstance(payload, list) else [payload]
                    for row in rows:
                        name = (row.get("name") or "").strip()
                        if not name:
                            raise CommandError(f"Invalid block row in {file_path}: missing name")
                        block_code = (row.get("block_code") or "").strip()
                        if block_code:
                            existing = ReportBlockLibrary.objects.filter(content__block_code=block_code).first()
                            if existing:
                                for field, value in {
                                    "name": name,
                                    "category": row.get("category") or "",
                                    "block_type": row.get("block_type") or "narrative",
                                    "content": row.get("content") or {},
                                }.items():
                                    setattr(existing, field, value)
                                existing.save(update_fields=["name", "category", "block_type", "content", "updated_at"])
                                stats["updated"] += 1
                                continue

                        _, created = ReportBlockLibrary.objects.update_or_create(
                            name=name,
                            defaults={
                                "category": row.get("category") or "",
                                "block_type": row.get("block_type") or "narrative",
                                "content": row.get("content") or {},
                            },
                        )
                        stats["created" if created else "updated"] += 1

                if dry_run:
                    raise _DryRunRollback()
        except _DryRunRollback:
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f"Block library import complete. created={stats['created']} updated={stats['updated']} dry_run={dry_run}"
            )
        )

    def _seed_files(self, path: Path):
        if not path.exists():
            raise CommandError(f"Block library path not found: {path}")
        if path.is_dir():
            files = sorted(path.glob("*.json"))
            if not files:
                raise CommandError(f"No block-library JSON files found under: {path}")
            return files
        return [path]
