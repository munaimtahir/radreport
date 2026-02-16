# RIMS RadReport — Dev Notes

## DB Reset (no important data)

Since the database has no critical data, a full reset is safe:

```bash
docker compose down -v
mkdir -p ./data/media
docker compose up -d --build
```

Then run migrations and seed (if not auto-run by entrypoint):

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python seed_data.py
```

## Caddy /media snippet

To serve uploaded media files (logos, receipts, etc.) via Caddy on the host, add a snippet to your Caddyfile. Adjust the path for your deployment server:

```
handle_path /media/* {
    root * /home/munaim/srv/apps/radreport/data/media
    file_server
}
```

Or with a specific site block:

```
rims.alshifalab.pk {
    # ... other directives ...
    handle_path /media/* {
        root * /home/munaim/srv/apps/radreport/data/media
        file_server
    }
}
```

## Printing endpoints mapping

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/printing/config/` | Merged org + receipt config (auth required) |
| PATCH | `/api/printing/config/` | Update both configs (admin required) |
| POST | `/api/printing/config/upload-report_logo/` | Upload report logo (`report_logo` file) |
| POST | `/api/printing/config/upload-receipt_logo/` | Upload receipt logo (`receipt_logo` file) |
| POST | `/api/printing/config/upload-receipt_banner/` | Upload receipt banner (`receipt_banner` file) |
| GET | `/api/printing/sequence/next?type=receipt&dry_run=1` | Preview next receipt number (admin) |

## ID formats (SequenceCounter)

| Key | Period | Format | Example |
|-----|--------|--------|---------|
| patient_mrn | YYYYMMDD | MR{period}{seq:04d} | MR202602150001 |
| patient_reg | YY | CCJ-{period}-{seq:04d} | CCJ-26-0001 |
| service_visit | YYMM | {period}-{seq:04d} | 2602-0001 |
| receipt | YYMM | {period}-{seq:04d} | 2602-0001 |

## Role seed (groups only)

Default: `seed_roles` creates groups only (`registration_desk`, `performance_desk`, `verification_desk`, `doctor`). No demo users.

To create demo users:

```bash
docker compose exec backend python manage.py seed_roles --with-demo-users
```

## Production Bootstrap

The production entrypoint calls `prod_bootstrap.sh` which runs:
- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`
- `python manage.py check`

If any step fails, the container exits with a non-zero code.

To run bootstrap manually:
```bash
docker compose exec backend /app/scripts/prod_bootstrap.sh
```
