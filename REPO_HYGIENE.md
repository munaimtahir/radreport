# Repo Hygiene & Organization

## 1. No Binary Dumps
- Do **NOT** commit `.zip`, `.gz`, `.sql`, `.dump`, or `.db` files to the repository.
- Use `db/seeds/` for initial data, or the configured S3 bucket for large assets.

## 2. Artifacts & Reports
- **Temporary Artifacts**: Store in `ARTIFACTS/`. This directory is git-ignored.
- **Permanent Reports**: Store in `REPORTS/`. This directory is tracked.
- **Logs**: Do not commit logs.

## 3. Adding New Templates
All new templates must be added to the canonical seed path:
- `backend/apps/reporting/seed_data/templates_v2/`

Do **NOT** add templates via:
- Random SQL dumps.
- `baseline_packs/` in the root.
- Manual database edits without a corresponding file in the seed path.

## 4. Environment Variables
- Never commit `.env` or files containing secrets.
- Maintain `.env.example` with safe defaults.
