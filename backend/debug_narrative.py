import os
import django
import json
import sys

# Setup Django environment
sys.path.append('/home/munaim/srv/apps/radreport/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.reporting.models import ReportTemplateV2
from apps.reporting.services.narrative_v2 import generate_narrative_v2

def test_narrative():
    # Load the template
    try:
        template = ReportTemplateV2.objects.get(code="USG_ABD_V1")
    except ReportTemplateV2.DoesNotExist:
        print("Template USG_ABD_V1 not found!")
        return

    print(f"Loaded template: {template.name}")
    print("Narrative Rules Sections:", len(template.narrative_rules.get("sections", [])))

    # Scenario 1: Full data (Happy Path)
    full_values = {
        "liv_visualized": "Satisfactory",
        "liv_size_cm": 14.5,
        "liv_contour": "Smooth",
        "liv_echogenicity": "Normal",
        "liv_echotexture": "Homogeneous",
        "gb_visualized": "Satisfactory",
        "gb_status": "Normal",
        "gb_wall_thickness_mm": 3,
        # ... just enough to trigger the first few rules
    }
    
    print("\n--- Scenario 1: Full Data ---")
    result_full = generate_narrative_v2(template, full_values)
    print(json.dumps(result_full, indent=2))

    # Scenario 2: Partial data (Missing size)
    partial_values = {
        "liv_visualized": "Satisfactory",
        # liv_size_cm MISSING
        "liv_contour": "Smooth",
        "liv_echogenicity": "Normal",
        "liv_echotexture": "Homogeneous",
    }

    print("\n--- Scenario 2: Partial Data (Missing liv_size_cm) ---")
    result_partial = generate_narrative_v2(template, partial_values)
    print(json.dumps(result_partial, indent=2))

if __name__ == "__main__":
    test_narrative()
