# Main Branch Rules & Constitution

## 1. Deployable State
The `main` branch must remain in a deployable state at all times.
- No broken builds.
- No failed tests.
- No regressions in core functionality.

## 2. V2 Templates Only
- **Legacy V1 reporting (V1 models, APIs, PDF generation, baseline packs) is strictly FORBIDDEN.**
- New reporting features must be implemented using the V2 architecture.

## 3. Canonical Seed Source
There is only ONE source of truth for seeding templates and blocks:
- **Block Library**: `backend/apps/reporting/seed_data/templates_v2/library/`
- **Activation Profiles**: `backend/apps/reporting/seed_data/templates_v2/activation/`

## 4. Forbidden Items
- No `baseline_packs/` at the repository root.
- No modules with broken imports.
- No random database dumps or ZIP files committed to the repo.

## 5. Definition of Done
A feature or fix is considered "Done" only when:
1. Seed dry-run passes: `python manage.py import_block_library --dry-run` and `python manage.py import_templates_v2 --dry-run`.
2. Unit tests pass (especially `apps/reporting`).
3. The "Verify Main" check passes.
