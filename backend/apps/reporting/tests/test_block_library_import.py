from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.reporting.models import ReportBlockLibrary


class BlockLibraryImportTests(TestCase):
    def setUp(self):
        ReportBlockLibrary.objects.all().delete()
        self.seed_dir = Path(__file__).resolve().parents[1] / "seed_data" / "block_library" / "phase2_v1.1"

    def test_dry_run_makes_no_writes(self):
        call_command("import_block_library_v1", "--dry-run", f"--path={self.seed_dir}")
        self.assertEqual(ReportBlockLibrary.objects.count(), 0)

    def test_import_creates_blocks(self):
        call_command("import_block_library_v1", f"--path={self.seed_dir}")
        self.assertGreater(ReportBlockLibrary.objects.count(), 0)

    def test_idempotent(self):
        call_command("import_block_library_v1", f"--path={self.seed_dir}")
        count1 = ReportBlockLibrary.objects.count()
        call_command("import_block_library_v1", f"--path={self.seed_dir}")
        count2 = ReportBlockLibrary.objects.count()
        self.assertEqual(count1, count2)
