# Backup and Restore Runbook

## Overview
This system provides live-safe backups for a Docker Compose Django/React/PostgreSQL stack.

Backups are stored under:
- `${PROJECT_ROOT}/backups/YYYY-MM-DD/`

Artifacts created:
- `db.sql.gz` (or `db.sql.gz.enc` when encryption key is set)
- `media.tar.gz` (or `.enc`)
- `infra.tar.gz` (or `.enc`)
- `app_commit.txt`
- `app_status.txt`
- `meta.json`
- `backup.log`
- `checksums.sha256`

## Automatic Backups
### Schedule
- Daily at 2:00 AM via cron.

### Install (idempotent)
```bash
./install_cron.sh
```

### Cron log
- `/var/log/app_backup_cron.log`
- Per-backup logs are inside each backup folder (`backup.log`).

## Manual Backup
```bash
./backup_full.sh --trigger manual --created-by admin_user --deletable
```

Useful options:
- `--force`: rebuild backup if the date folder already exists.
- `BACKUP_ROOT=/path`: override default backup location.

## Restore
Restore is destructive (DB schema reset + file replacement).

Dry run:
```bash
./restore_full.sh 2026-02-11 --dry-run
```

Real restore:
```bash
./restore_full.sh 2026-02-11 --yes
```

Restore from explicit folder:
```bash
./restore_full.sh /srv/apps/radreport/backups/2026-02-11 --yes
```

Optional flag:
- `--allow-system-caddy-overwrite`: applies `/etc/caddy/Caddyfile` from backup (otherwise only staged and logged).

## Encryption (Optional)
If `BACKUP_ENCRYPTION_KEY` is set, artifacts are encrypted with OpenSSL AES-256-CBC:

```bash
export BACKUP_ENCRYPTION_KEY='your-strong-secret'
./backup_full.sh --trigger manual --created-by security_admin
```

Notes:
- Encrypted artifacts are saved as `*.enc`.
- Restore requires the same `BACKUP_ENCRYPTION_KEY`.
- Keep encryption key outside git and outside backup archives.

## Cloud Sync (rclone)
API and admin UI use rclone remotes.

Environment variables:
- `BACKUP_RCLONE_REMOTE` (default: `offsite`)
- `BACKUP_RCLONE_PATH` (default: `radreport-backups`)

Example:
```bash
export BACKUP_RCLONE_REMOTE=offsite
export BACKUP_RCLONE_PATH=lims-backups
```

Server setup:
```bash
rclone config
rclone listremotes
rclone lsd offsite:lims-backups
```

Supported providers are anything rclone supports (Google Drive, S3, B2, Dropbox, etc).

## Disaster Recovery Checklist
1. Confirm VPS health (disk, Docker daemon, Compose services).
2. Identify backup folder and verify with `./verify_backup.sh YYYY-MM-DD`.
3. Run dry-run restore first.
4. Run actual restore with `--yes`.
5. Verify smoke checks:
- DB connectivity
- API health endpoint
- media/infrastructure files
6. Reload Caddy if config changed.
7. Document restored backup id/date/commit hash in incident notes.

## Security Notes
- No DB credentials are hardcoded.
- DB backup runs from detected Postgres service via `docker compose exec -T`.
- Restore requires explicit confirmation (`RESTORE NOW` unless `--yes`).
- API restore is superuser-only and audited.
- Restrict filesystem permissions on backup root (`750` recommended).

## Monthly Test-Restore Procedure
1. Create a fresh manual backup.
2. Provision staging environment.
3. Import/export round-trip test through API/UI.
4. Execute `restore_full.sh --dry-run` on staging backup.
5. Execute real staging restore and run smoke tests.
6. Record pass/fail with date and owner.

## Verification Commands
```bash
./verify_backup.sh 2026-02-11
crontab -l
ls -la backups/
```
