# Caddyfile Snippet for RIMS Production

This snippet should be added to your system Caddyfile (typically `/etc/caddy/Caddyfile`).

## Complete RIMS Block

```caddy
# =========================
# RIMS (Radiology Information Management System) - React + Django
# Domain: rims.alshifalab.pk (or your domain)
# Frontend container: 127.0.0.1:8081 (nginx serving built React app)
# Backend: 127.0.0.1:8015
# =========================
rims.alshifalab.pk {
    encode gzip zstd

    # ---- Backend API routes ----
    handle /api/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # ---- Django Admin ----
    handle /admin/* {
        reverse_proxy 127.0.0.1:8015 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }

    # ---- Health endpoints ----
    handle /health* {
        reverse_proxy 127.0.0.1:8015
    }
    handle /healthz* {
        reverse_proxy 127.0.0.1:8015
    }

    # ---- Static files (served via Django in container) ----
    handle /static/* {
        reverse_proxy 127.0.0.1:8015
    }

    # ---- Media files (served via Django in container) ----
    handle /media/* {
        reverse_proxy 127.0.0.1:8015
    }

    # ---- Optional API docs / schema ----
    handle_path /docs* {
        reverse_proxy 127.0.0.1:8015
    }
    handle_path /schema* {
        reverse_proxy 127.0.0.1:8015
    }

    # ---- Frontend SPA (proxied to frontend nginx container) ----
    @notBackend {
        not path /api/*
        not path /admin/*
        not path /health*
        not path /healthz*
        not path /static/*
        not path /media/*
        not path /docs*
        not path /schema*
    }
    handle @notBackend {
        reverse_proxy 127.0.0.1:8081 {
            header_up Host {host}
            header_up X-Real-IP {remote}
            header_up X-Forwarded-For {remote}
            header_up X-Forwarded-Proto {scheme}
        }
    }
}
```

## After Adding the Snippet

Reload Caddy to apply changes:

```bash
sudo systemctl reload caddy
```

Check Caddy status:

```bash
sudo systemctl status caddy
```

View Caddy logs:

```bash
sudo journalctl -u caddy -f
```

## Customization

### Use Your Domain

Replace `rims.alshifalab.pk` with your actual domain:

```caddy
your.domain.com {
    # ... rest of configuration
}
```

### Multiple Domains

Add multiple domains separated by commas:

```caddy
rims.alshifalab.pk, rims.yourdomain.com {
    # ... rest of configuration
}
```

### Alternative: Serve Frontend Static Files Directly

If you prefer to serve frontend files directly from Caddy instead of proxying to nginx container:

1. Build and copy frontend files:

```bash
cd frontend
npm run build
sudo mkdir -p /var/www/rims
sudo cp -r dist/* /var/www/rims/
```

2. Replace the frontend section in Caddyfile:

```caddy
    # ---- Frontend SPA (served directly by Caddy) ----
    @notBackend {
        not path /api/*
        not path /admin/*
        not path /health*
        not path /healthz*
        not path /static/*
        not path /media/*
        not path /docs*
        not path /schema*
    }
    handle @notBackend {
        root * /var/www/rims
        try_files {path} {path}/ /index.html
        file_server
    }
```

3. Optionally disable the frontend container in docker-compose.yml

## Testing the Configuration

Test Caddy configuration syntax before reloading:

```bash
caddy validate --config /etc/caddy/Caddyfile
```

Test endpoints after deployment:

```bash
# Backend health
curl https://rims.alshifalab.pk/api/health/

# Frontend
curl -I https://rims.alshifalab.pk/

# Admin
curl -I https://rims.alshifalab.pk/admin/
```

## Troubleshooting

### Certificate Issues

If Caddy can't obtain SSL certificates:

1. Verify DNS points to your server:
   ```bash
   dig rims.alshifalab.pk
   ```

2. Ensure ports 80 and 443 are open:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. Check Caddy logs:
   ```bash
   sudo journalctl -u caddy --no-pager -n 100
   ```

### Proxy Errors

If you get 502 Bad Gateway:

1. Verify backend is running:
   ```bash
   curl http://127.0.0.1:8015/api/health/
   ```

2. Verify frontend is running:
   ```bash
   curl http://127.0.0.1:8081/
   ```

3. Check Docker containers:
   ```bash
   docker-compose ps
   ```
