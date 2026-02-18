"""
Tests for USG_ABD_V1 template narrative generation with expanded abnormal fields.

Fixtures:
1) Normal abdomen - all organs visualized, no abnormal findings
2) Gallstones + mild CBD dilatation
3) Right moderate hydro + ureteric stone

Validates:
- Template renders even when new fields are missing (optional placeholders)
- Narrative generation does not crash with partial abnormal entry
- Not-visualized suppression prevents contradictions
"""

import json
from pathlib import Path

from django.test import TestCase

from apps.reporting.models import ReportTemplateV2
from apps.reporting.services.narrative_v2 import generate_narrative_v2


def _load_usg_abd_template():
    """Load USG_ABD_V1 template from seed data."""
    seed_path = Path(__file__).resolve().parents[1] / "seed_data" / "templates_v2" / "library" / "phase2_v1.1" / "USG_ABD_V1.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    template, _ = ReportTemplateV2.objects.update_or_create(
        code=data["code"],
        defaults={
            "name": data["name"],
            "modality": data["modality"],
            "status": data.get("status", "active"),
            "json_schema": data["json_schema"],
            "ui_schema": data["ui_schema"],
            "narrative_rules": data["narrative_rules"],
        },
    )
    return template


class USGABDNarrativeTests(TestCase):
    """Tests for USG Abdomen template narrative with expanded fields."""

    def setUp(self):
        self.template = _load_usg_abd_template()

    def test_fixture_1_normal_abdomen(self):
        """Fixture 1: Normal abdomen - minimal required fields, no abnormals."""
        values = {
            "liv_visualized": "Satisfactory",
            "gb_visualized": "Satisfactory",
            "kid_r_visualized": "Satisfactory",
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        self.assertIn("narrative_by_organ", result)
        self.assertIn("narrative_text", result)
        self.assertIn("sections", result)
        self.assertIn("impression", result)
        # Should not crash; new fields are optional
        self.assertIsInstance(result["narrative_text"], str)

    def test_fixture_2_gallstones_cbd_dilatation(self):
        """Fixture 2: Gallstones + mild CBD dilatation."""
        values = {
            "liv_visualized": "Satisfactory",
            "gb_visualized": "Satisfactory",
            "gb_stones_present": True,
            "gb_largest_stone_mm": 8,
            "gb_cbd_diameter_mm": 7,
            "cbd_dilated": True,
            "kid_r_visualized": "Satisfactory",
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        self.assertIn("narrative_by_organ", result)
        self.assertIn("narrative_text", result)
        narrative_text = result["narrative_text"].lower()
        self.assertIn("calculus", narrative_text)
        self.assertIn("cholelithiasis", str(result.get("impression", [])).lower())
        self.assertIn("dilat", narrative_text)

    def test_fixture_3_right_moderate_hydro_ureter_stone(self):
        """Fixture 3: Right moderate hydro + ureteric stone."""
        values = {
            "liv_visualized": "Satisfactory",
            "gb_visualized": "Satisfactory",
            "kid_r_visualized": "Satisfactory",
            "kid_r_hydronephrosis_grade": 2,
            "kid_r_hydro_grade": "moderate",
            "kid_r_ureter_stone_present": True,
            "kid_r_ureter_stone_mm": 5,
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        self.assertIn("narrative_by_organ", result)
        self.assertIn("narrative_text", result)
        narrative_text = result["narrative_text"].lower()
        self.assertIn("hydronephrosis", narrative_text)
        self.assertIn("ureteric", narrative_text)
        impression_str = " ".join(result.get("impression", [])).lower()
        self.assertTrue(
            "hydronephrosis" in impression_str or "ureteric" in impression_str or "calculi" in impression_str,
            f"Expected impression to mention hydro or ureteric; got {result.get('impression')}",
        )

    def test_partial_abnormal_does_not_crash(self):
        """Partial abnormal entry (e.g. stone present but no mm) should not crash."""
        values = {
            "liv_visualized": "Satisfactory",
            "gb_visualized": "Satisfactory",
            "gb_stones_present": True,
            "kid_r_visualized": "Satisfactory",
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        self.assertIn("narrative_text", result)
        self.assertIsInstance(result["narrative_text"], str)

    def test_post_cholecystectomy_suppresses_stone_rules(self):
        """Post-cholecystectomy: GB not visualized, no stone/sludge statements."""
        values = {
            "liv_visualized": "Satisfactory",
            "gb_visualized": "Post-cholecystectomy",
            "gb_post_cholecystectomy": True,
            "kid_r_visualized": "Satisfactory",
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        narrative_text = result["narrative_text"].lower()
        self.assertIn("post-cholecystectomy", narrative_text)
        self.assertNotIn("calculus", narrative_text)
        self.assertNotIn("stone", narrative_text)
        self.assertNotIn("sludge", narrative_text)

    def test_liver_not_visualized_suppresses_contradictions(self):
        """When liver is not visualized, no size/echotexture/lesion statements."""
        values = {
            "liv_visualized": "No",
            "gb_visualized": "Satisfactory",
            "kid_r_visualized": "Satisfactory",
            "kid_l_visualized": "Satisfactory",
        }
        result = generate_narrative_v2(self.template, values)
        narrative_text = result["narrative_text"].lower()
        self.assertIn("not visualized", narrative_text)
        # Composer visibility dominance: liver section should be dominated by not visualized
        liver_section = next((s for s in result.get("sections", []) if "Liver" in s.get("title", "")), {})
        lines = " ".join(liver_section.get("lines", [])).lower()
        self.assertIn("not visualized", lines)

    def test_empty_values_does_not_crash(self):
        """Empty/minimal values_json should not crash."""
        result = generate_narrative_v2(self.template, {})
        self.assertIn("narrative_text", result)
        self.assertIsInstance(result["narrative_text"], str)
