# Template Presets

This folder stores JSON presets that can be imported into the RIMS Template system.

## Import: Ultrasound Abdomen (Structured)

From `backend/` run:

```bash
python manage.py import_template_json \
  --path docs/presets/templates/abdomen_usg_v1.json \
  --replace \
  --publish \
  --link-service "Abdominal Ultrasound"
```

### Notes
- `--replace` deletes existing sections for this template and re-imports fresh (recommended for upgrades).
- `--publish` creates a new `TemplateVersion` snapshot so the UI/ReportEditor can render it.
- `--link-service` is optional. If your project has `apps.catalog.Service`, it sets the service's `default_template`.

## Upgrade flow (v2)
1. Copy the JSON and modify fields/sections
2. Re-run the import command with `--replace --publish`
3. A new TemplateVersion is created (v2, v3, etc.)
