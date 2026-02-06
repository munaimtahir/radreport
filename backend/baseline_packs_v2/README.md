# Baseline Packs V2

This folder contains the baseline configuration for Reporting V2.

## Files

- `templates_v2.json`: Definitions of V2 templates (JSON Schema + UI Schema + Narrative Rules).
- `service_template_v2_links.csv`: Mapping between Service Codes (from Catalog) and Template Codes.

## Usage

To import these packs into the system, run:

```bash
python manage.py import_templates_v2 \
  --templates baseline_packs_v2/templates_v2.json \
  --mappings baseline_packs_v2/service_template_v2_links.csv \
  --activate
```
