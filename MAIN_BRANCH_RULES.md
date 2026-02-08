# Main Branch Constitution

- Main is deployable at all times; no broken builds or failing checks are allowed to land.
- V2 templates only. Legacy V1 reporting (models/APIs/PDF configs/baseline packs) is forbidden.
- Single canonical seed source path:
  - `backend/apps/reporting/seed_data/templates_v2/library/`
  - `backend/apps/reporting/seed_data/templates_v2/activation/`
- Forbidden items: `baseline_packs/` at repo root, modules with broken imports, random dumps/zips.
- Definition of Done: seed dry-run PASS (`python manage.py import_block_library --dry-run` and `python manage.py import_templates_v2 --dry-run`) + tests PASS.
