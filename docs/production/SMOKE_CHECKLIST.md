# Production smoke checklist (USG only, no browser)

> Replace `<domain>`, `<token>`, and `<pdf-path>` as needed.

1) **External health check (no auth)**

```bash
curl -fsS https://<domain>/api/health/
```

2) **Authenticated health check (JWT)**

```bash
curl -fsS \
  -H "Authorization: Bearer <token>" \
  https://<domain>/api/health/auth/
```

3) **Run USG smoke workflow (backend host/container)**

```bash
python manage.py smoke_prod_usg
```

4) **Find the generated PDF path**

The smoke output prints the published PDF path (relative to `/media/`). Copy the
path into the next command as `<pdf-path>`.

5) **Verify Caddy serves the PDF directly**

```bash
curl -I https://<domain>/media/<pdf-path>
```

6) **Optional: legacy PDF route (if still used)**

```bash
curl -I https://<domain>/api/pdf/receipt/<visit_id>/
```

This route should either redirect to `/media/` or not be required in production.
