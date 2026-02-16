# Backup Cloud Readiness (rclone)

This document describes how to configure and verify rclone for cloud backup operations.

## rclone Installation

rclone is installed in the backend container via the Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    rclone \
    ...
```

## rclone Configuration

### Option 1: Bind Mount Configuration File (Recommended)

Mount the rclone configuration file from the host into the backend container:

**docker-compose.prod.yml:**
```yaml
services:
  backend:
    volumes:
      # Mount rclone config from host
      - /root/.config/rclone/rclone.conf:/root/.config/rclone/rclone.conf:ro
      # ... other volumes
```

**On the host**, ensure the rclone config exists:
```bash
# Configure rclone remote (run on host or in container)
rclone config

# This creates: /root/.config/rclone/rclone.conf
```

### Option 2: Environment Variables

Some rclone remotes can be configured via environment variables. See [rclone documentation](https://rclone.org/docs/#environment-variables) for details.

## Verification

### Check rclone Version

Verify rclone is available in the container:

```bash
docker compose exec backend rclone version
```

Expected output:
```
rclone v1.xx.x
- os/arch: linux/amd64
- go version: go1.xx.x
```

### Test Remote Connection

If `BACKUP_RCLONE_REMOTE` and `BACKUP_RCLONE_PATH` environment variables are set:

```bash
docker compose exec backend bash -c '
  export BACKUP_RCLONE_REMOTE=${BACKUP_RCLONE_REMOTE:-offsite}
  export BACKUP_RCLONE_PATH=${BACKUP_RCLONE_PATH:-radreport-backups}
  rclone lsd ${BACKUP_RCLONE_REMOTE}:${BACKUP_RCLONE_PATH}/
'
```

Or test via the API endpoint:

```bash
# Get auth token first
TOKEN=$(curl -s -X POST https://rims.alshifalab.pk/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | \
  grep -o '"access":"[^"]*' | cut -d'"' -f4)

# Test cloud connection
curl -X POST https://rims.alshifalab.pk/api/backups/cloud/test/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"remote_name":"offsite","remote_path":"radreport-backups"}'
```

## Environment Variables

Configure these in your `docker-compose.prod.yml` or `.env`:

```yaml
environment:
  BACKUP_RCLONE_REMOTE: ${BACKUP_RCLONE_REMOTE:-offsite}
  BACKUP_RCLONE_PATH: ${BACKUP_RCLONE_PATH:-radreport-backups}
```

## Backup Operations

Once configured, backups can be uploaded to cloud storage via:

1. **API endpoint**: `POST /api/backups/{backup_id}/upload/`
2. **Management command**: `python manage.py backup_run --upload`
3. **Frontend UI**: Backup Operations page → Upload button

## Troubleshooting

### rclone not found

If `rclone version` fails, ensure the Dockerfile includes rclone installation and the container is rebuilt.

### Permission denied

If rclone config file access fails:
- Ensure the bind mount path is correct
- Check file permissions: `chmod 600 /root/.config/rclone/rclone.conf`
- Verify the container user has read access

### Remote not found

If `rclone lsd` fails with "remote not found":
- Verify the remote name matches your config
- Check the config file is mounted correctly
- Run `rclone config show` to list configured remotes

### Connection timeout

If cloud operations timeout:
- Verify network connectivity from container
- Check firewall rules
- Test rclone connection from host first: `rclone lsd offsite:`
