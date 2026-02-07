# Seeding & Data State

This project uses a deterministic, idempotent seeding strategy for V2 reporting.

## Canonical Commands

Run these commands from the `backend/` directory (or using `python backend/manage.py` from root):

### 1. Import Block Library (Dry Run)
Check for validity without applying changes:
```bash
python manage.py import_block_library --dry-run
```

### 2. Import Templates V2 (Dry Run)
Check for validity of templates and activation profiles:
```bash
python manage.py import_templates_v2 --dry-run
```

### 3. Full Seeding (Apply Changes)
To apply the changes to the database:
```bash
python manage.py seed_reporting_v2
```
(Note: `seed_reporting_v2` runs both imports in order. If `--dry-run` is supported by the command wrapper, use it; otherwise rely on the individual dry-runs above).

## Idempotency
All seed commands are designed to be **idempotent**. It is safe to run them repeatedly. They will:
- Create missing items.
- Update existing items if the source file has changed.
- **Not** duplicated items improperly (keyed by unique identifiers).

## Adding New Content
1. Place new JSON/YAML definitions in `backend/apps/reporting/seed_data/templates_v2/`.
2. Verify with dry-run commands.
3. Commit the changes.
