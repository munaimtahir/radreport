from django.test import TestCase
import re

from apps.reporting.services.narrative_composer import NarrativeAtom, compose_narrative, compose_organ_paragraph


class NarrativeComposerTests(TestCase):
    def _sentence_count(self, text: str) -> int:
        return len(re.findall(r"[.!?](?:\\s|$)", text))

    def test_kidneys_bilateral_measurement_and_negatives(self):
        atoms = [
            NarrativeAtom(organ="kidneys", side="R", kind="measurement", priority=2, text="Right kidney measures 10.2 cm"),
            NarrativeAtom(organ="kidneys", side="L", kind="measurement", priority=3, text="Left kidney measures 10.0 cm"),
            NarrativeAtom(organ="kidneys", side="R", kind="status", priority=4, text="Corticomedullary differentiation is preserved"),
            NarrativeAtom(organ="kidneys", side="R", kind="negative", priority=5, text="No hydronephrosis"),
            NarrativeAtom(organ="kidneys", side="L", kind="negative", priority=6, text="No hydronephrosis"),
            NarrativeAtom(organ="kidneys", side="L", kind="negative", priority=7, text="No renal calculi"),
        ]

        paragraph = compose_organ_paragraph(atoms, "kidneys")
        self.assertIn("Both kidneys measure 10.2 cm (right) and 10.0 cm (left)", paragraph)
        self.assertIn("No hydronephrosis or renal calculi.", paragraph)
        self.assertLessEqual(self._sentence_count(paragraph), 2)

    def test_gallbladder_cbd_is_merged(self):
        atoms = [
            NarrativeAtom(organ="gallbladder_cbd", side="N", kind="status", priority=1, text="Gallbladder is unremarkable"),
            NarrativeAtom(organ="gallbladder_cbd", side="N", kind="negative", priority=2, text="No wall thickening"),
            NarrativeAtom(organ="gallbladder_cbd", side="N", kind="status", priority=3, text="Common bile duct is not dilated"),
        ]
        paragraph = compose_organ_paragraph(atoms, "gallbladder_cbd")
        self.assertIn("The gallbladder", paragraph)
        self.assertIn("and the CBD is not dilated", paragraph)
        self.assertLessEqual(self._sentence_count(paragraph), 2)

    def test_dedupe_negative(self):
        atoms = [
            NarrativeAtom(organ="kidneys", side="R", kind="negative", priority=1, text="No hydronephrosis"),
            NarrativeAtom(organ="kidneys", side="L", kind="negative", priority=2, text="No hydronephrosis"),
        ]
        paragraph = compose_organ_paragraph(atoms, "kidneys")
        self.assertEqual(paragraph.lower().count("hydronephrosis"), 1)

    def test_stable_order_with_shuffled_input(self):
        narrative_json = {
            "sections": [
                {
                    "title": "Left Kidney",
                    "lines": ["Left kidney measures 10.0 cm", "No hydronephrosis"],
                },
                {
                    "title": "Liver",
                    "lines": ["Liver is normal", "No focal lesion"],
                },
                {
                    "title": "Right Kidney",
                    "lines": ["Right kidney measures 10.2 cm", "No hydronephrosis"],
                },
            ]
        }

        composed = compose_narrative(narrative_json)
        organs = [item["organ"] for item in composed["narrative_by_organ"]]
        self.assertEqual(organs, ["liver", "kidneys"])
        self.assertTrue(composed["narrative_text"].startswith("Liver:"))
