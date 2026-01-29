# Settings Menu Fix Report

## Incident Summary
- **Symptom:** “Settings menu disappeared” after redeploy while Settings page still exists.
- **Scope:** React frontend sidebar/menu rendering in `frontend/src/ui/App.tsx`.

## Phase 1 — Stale Frontend Build Checks
- `/etc/caddy/Caddyfile` not present; Caddy validation/reload cannot be executed on this host.
- `nginx` binary not found; no nginx config to inspect.
- Repo `Caddyfile` shows RIMS frontend is reverse-proxied to `127.0.0.1:8081` (container). Evidence captured in `artifacts/proxy_check.log`.
- Public domain response for `https://rims.alshifalab.pk/` and `https://rims.alshifalab.pk/receipt-settings` returns `200` with `last-modified` headers; evidence in `artifacts/proxy_check.log`.
- Local build output exists in `frontend/dist` with fresh timestamps after rebuild; evidence appended in `artifacts/proxy_check.log`.

**Conclusion:** Proxy is configured for reverse proxy (not static path). No evidence of a stale static root path on this host; the menu disappearance is consistent with a UI nav omission rather than a stale `dist` path.

## Phase 2 — Menu/Route Location
- Navigation menu is rendered inside `frontend/src/ui/App.tsx`.
- Settings-related routes exist in the same file (`/receipt-settings`), but the Settings link was not present in the Settings menu block.
- Evidence captured in:
  - `artifacts/settings_grep.txt`
  - `artifacts/routes_extract.txt`
  - `artifacts/menu_extract.txt`

## Phase 3 — Gating Condition
- Menu section for settings is wrapped in `canAdmin`, which is derived from `user?.is_superuser` in `App.tsx`.
- The user data is fetched from `/api/auth/me/` and includes `is_superuser` and `groups`.
- The Settings page (`/receipt-settings`) is not gated by `canAdmin`, but its navigation link had been removed/commented out, causing the menu item to disappear.

## Phase 4 — Minimal Fix Applied
- Restored a `Receipt Settings` menu link inside the existing **SETTINGS** nav block for admins (superusers). This is the smallest UI-only change to expose the existing Settings page.

## Phase 5 — Frontend Rebuild + Redeploy
- `npm ci` and `npm run build` executed; logs in `artifacts/frontend_build.log`.
- **Redeploy attempt failed** due to `docker` not being installed in this environment, so the rebuilt assets could not be pushed into the running frontend container here.

## Phase 6 — End-to-End Verification
- Backend token fetch to `http://127.0.0.1:8015/api/auth/token/` failed (connection refused). Logged in `artifacts/backend_check.log`.
- Domain-level SPA route check for `/receipt-settings` returned `200` (SPA entry), recorded in `artifacts/proxy_check.log`.

## Root Cause
- The Settings menu item for the existing `/receipt-settings` page was removed/hidden in the sidebar navigation configuration during redeploy. The route still exists, but the menu entry was missing, so superadmins could not see it.

## Changes Made
- Reintroduced `Receipt Settings` navigation link in the Settings section (admin-only) in `frontend/src/ui/App.tsx`.

## Verification Status
- **Frontend build completed** (log captured).
- **Frontend container redeploy not possible** in this environment (`docker` missing).
- **Backend auth check failed** due to local service not running.

## Remaining Risks / Follow-ups
- Deploy the rebuilt frontend image to the `rims_frontend_prod` container and verify the Settings menu appears for a superadmin.
- Run the backend auth check and validate `/api/auth/me/` returns `is_superuser: true` for the superadmin account.
