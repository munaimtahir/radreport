from django.test import TestCase
from apps.reporting.services.narrative_v2 import generate_narrative_v2
from apps.reporting.models import ReportTemplateV2

class NarrativeV2LogicTests(TestCase):
    def setUp(self):
        self.template = ReportTemplateV2.objects.create(
            code="TEST_V2",
            name="Test Template",
            modality="Test",
            json_schema={
                "type": "object", 
                "properties": {
                    "rk_size": {"type": "number"},
                    "lk_size": {"type": "number"},
                    "stones": {"type": "boolean"},
                    "calc": {"type": "string"},
                }
            },
            is_frozen=False
        )

    def test_computed_fields(self):
        self.template.narrative_rules = {
            "computed_fields": {
                "renal_symmetry": "abs(rk_size - lk_size)"
            },
            "sections": [
                {
                    "title": "Findings",
                    "content": ["Asymmetry: {{renal_symmetry}}"]
                }
            ]
        }
        values = {"rk_size": 10, "lk_size": 12, "stones": False}
        result = generate_narrative_v2(self.template, values)
        
        sections = result.get("sections", [])
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["lines"][0], "Asymmetry: 2.0")

    def test_conditional_logic_if_else(self):
        self.template.narrative_rules = {
            "sections": [
                {
                    "title": "Findings",
                    "content": [
                        {
                            "if": {"field": "stones", "equals": True},
                            "then": "Stones seen.",
                            "else": "No stones."
                        }
                    ]
                }
            ]
        }
        
        # Case 1: True
        res1 = generate_narrative_v2(self.template, {"stones": True})
        self.assertEqual(res1["sections"][0]["lines"][0], "Stones seen.")
        
        # Case 2: False
        res2 = generate_narrative_v2(self.template, {"stones": False})
        self.assertEqual(res2["sections"][0]["lines"][0], "No stones.")

    def test_operators(self):
        self.template.narrative_rules = {
            "sections": [{
                "title": "Findings",
                "content": [
                    {
                        "if": {"field": "rk_size", "gt": 10},
                        "then": "Enlarged."
                    }
                ]
            }]
        }
        res1 = generate_narrative_v2(self.template, {"rk_size": 11})
        self.assertEqual(res1["sections"][0]["lines"][0], "Enlarged.")
        
        res2 = generate_narrative_v2(self.template, {"rk_size": 10})
        self.assertEqual(len(res2.get("sections", [])), 0)

    def test_impression_synthesis(self):
        self.template.narrative_rules = {
            "impression_rules": [
                {
                    "priority": 1,
                    "when": {"field": "stones", "equals": True},
                    "text": "Calculi.",
                    "continue": True
                },
                {
                    "priority": 2,
                    "when": {"field": "rk_size", "gt": 12},
                    "text": "Renal enlargement."
                }
            ]
        }
        
        values = {"stones": True, "rk_size": 13}
        result = generate_narrative_v2(self.template, values)
        
        impression = result.get("impression", [])
        self.assertEqual(len(impression), 2)
        self.assertEqual(impression[0], "Calculi.")
        self.assertEqual(impression[1], "Renal enlargement.")
