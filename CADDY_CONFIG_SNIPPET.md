# Caddy Configuration Snippet for RIMS

## ✅ Configuration Added to `/etc/caddy/Caddyfile`

The following configuration block has been added to your Caddyfile:

```caddy
# =========================
# RIMS (Radiology Information Management System) - React + Django
# Domain: rims.alshifalab.pk
# Frontend container: 127.0.0.1:8081 (nginx serving built React app)
# Backend: 127.0.0.1:8015
# =========================
rims.alshifalab.pk {
	encode gzip zstd

	# ---- Backend routes ----
	handle /api/* {
		reverse_proxy 127.0.0.1:8015 {
			header_up Host {host}
			header_up X-Real-IP {remote}
		}
	}

	handle /admin/* {
		reverse_proxy 127.0.0.1:8015 {
			header_up Host {host}
			header_up X-Real-IP {remote}
		}
	}

	# Health endpoints
	handle /health* {
		reverse_proxy 127.0.0.1:8015
	}
	handle /healthz* {
		reverse_proxy 127.0.0.1:8015
	}

	# Static + media
	handle /static/* {
		reverse_proxy 127.0.0.1:8015
	}
	handle /media/* {
		reverse_proxy 127.0.0.1:8015
	}

	# API docs / schema
	handle_path /docs* {
		reverse_proxy 127.0.0.1:8015
	}
	handle_path /schema* {
		reverse_proxy 127.0.0.1:8015
	}

	# ---- Frontend SPA ----
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
		}
	}
}
```

## ✅ Configuration Applied

1. ✅ **Validated the configuration:**
   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   ```
   Result: Valid configuration

2. ✅ **Reloaded Caddy:**
   ```bash
   sudo systemctl reload caddy
   ```
   Result: Successfully reloaded

3. **Check status:**
   ```bash
   sudo systemctl status caddy
   ```

4. **View logs:**
   ```bash
   tail -f /home/munaim/srv/proxy/caddy/logs/caddy.log
   ```

## Notes

- ✅ Domain: `rims.alshifalab.pk` (DNS configured and propagated)
- ✅ Backend port: `8015` (ready for Django/Gunicorn)
- ✅ Frontend port: `8081` (ready for nginx container)
- ✅ Caddy will automatically obtain SSL certificate via Let's Encrypt on first request
- ✅ The configuration follows the same pattern as your SIMS setup
