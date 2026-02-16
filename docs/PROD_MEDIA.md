# Production Media Contract

This document defines the canonical media file handling for production deployments.

## Canonical Host Path

Media files are stored at:
- **Container path**: `/app/media` (inside backend container)
- **Host bind mount**: Configured via Docker Compose volume mapping
- **Canonical host path**: `/home/munaim/srv/apps/radreport/data/media` (adjust for your deployment)

## Caddy Configuration

To serve media files via Caddy on the host, add the following snippet to your Caddyfile:

```caddy
rims.alshifalab.pk {
    # ... other directives ...
    
    # Media files - served directly from host filesystem
    handle /media/* {
        root * /home/munaim/srv/apps/radreport/data/media
        file_server
        header Cache-Control "public, max-age=604800"
    }
    
    # API endpoints - proxied to backend container
    handle /api/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
            header_up X-Forwarded-Host {host}
        }
    }
    
    # Frontend - proxied to frontend container
    handle {
        reverse_proxy 127.0.0.1:8081 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

**Important**: Adjust the `root` path to match your deployment server's actual media directory path.

## Docker Compose Volume Mapping

Ensure your `docker-compose.prod.yml` maps the media volume correctly:

```yaml
services:
  backend:
    volumes:
      # Bind mount media for host Caddy to serve /media
      - ./data/media:/app/media
```

Or use a named volume and bind mount it on the host:

```yaml
volumes:
  PROD_radreport_media_data:
    name: PROD_radreport_media_data
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/munaim/srv/apps/radreport/data/media
```

## Verification

To verify media files are accessible via Caddy:

```bash
# Upload a test file via API (e.g., logo upload endpoint)
# Then test the media URL:
curl -I https://rims.alshifalab.pk/media/organization/logos/report_logo.png

# Expected: HTTP 200 OK
```

Or use the smoke test script with optional media check:

```bash
MEDIA_TEST_URL=https://rims.alshifalab.pk/media/organization/logos/report_logo.png \
  BASE_URL=https://rims.alshifalab.pk \
  ADMIN_USER=admin \
  ADMIN_PASS=password \
  ./scripts/smoke_prod.sh
```

## Media File Types

The following media files are stored and served via `/media/`:

- **Organization logos**: `/media/organization/logos/report_logo.*`
- **Receipt branding**: `/media/receipts/logos/receipt_logo.*`, `/media/receipts/banners/receipt_banner.*`
- **Uploaded documents**: `/media/documents/...`
- **Generated PDFs**: `/media/reports/...`, `/media/receipts/...`

All media URLs are relative to the `MEDIA_URL` setting (`/media/` by default).
