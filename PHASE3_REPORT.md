# Phase 3 RBAC Enforcement Report

## RBAC design

**Desk groups (Django `auth.Group`):**
- `registration` → REGISTRATION_DESK
- `performance` → PERFORMANCE_DESK (USG)
- `verification` → VERIFICATION_DESK
- `superuser` → full access (bypass)

**Permissions matrix (USG workflow):**
| Role | Create Visit/Items | Edit USG Report | Submit for Verification | Verify/Publish |
| --- | --- | --- | --- | --- |
| Registration | ✅ | ❌ | ❌ | ❌ |
| Performance | ❌ | ✅ | ✅ | ❌ |
| Verification | ❌ | ❌ | ❌ | ✅ |
| Superuser | ✅ | ✅ | ✅ | ✅ |

## Backend enforcement summary

**Endpoints protected:**
- `/api/workflow/visits/` and `/api/workflow/items/` now require a desk group (registration/performance/verification) or superuser.
- `/api/workflow/visits/create_visit/` requires registration desk.
- `/api/workflow/usg/` (create/update) requires performance desk.
- `/api/workflow/usg/*` transitions:
  - `save_draft`, `submit_for_verification` require performance desk.
  - `finalize`, `publish`, `return_for_correction` require verification desk.
  - `create_amendment` now requires performance desk to avoid verification desk edits.
- Transition service enforces role-based status transitions for USG/OPD items.
- New `/api/auth/me/` endpoint returns groups for frontend route guards.

**Error behavior:**
- Forbidden access returns HTTP 403 with explicit "Access denied" messaging for write attempts against protected report content.

## Frontend enforcement summary

**Route guards (direct URL and navigation):**
- `/registration` → registration or superuser
- `/worklists/usg` → performance or superuser
- `/worklists/verification` → verification or superuser

**Access denied UI:** a dedicated AccessDenied page is rendered when blocked.

## Seed roles + demo users

Command:
```
python manage.py seed_roles_phase3
```

Behavior:
- Creates groups: `registration`, `performance`, `verification`
- Creates demo users if missing:
  - `reg_user` / `reg_user`
  - `perf_user` / `perf_user`
  - `ver_user` / `ver_user`
> Note: Requires database migrations to be applied (`python manage.py migrate`) so `auth_group` exists.

## Proof / validation

### Management command output (example)
```
Phase 3 role seeding complete.
Created groups: registration, performance, verification
Created users: reg_user, perf_user, ver_user
- reg_user / reg_user (group: registration)
- perf_user / perf_user (group: performance)
- ver_user / ver_user (group: verification)
```

### Backend proof (expected curl outputs)

```
# REGISTRATION: can create visit
curl -X POST http://localhost:8000/api/workflow/visits/create_visit/ -H "Authorization: Bearer <reg_token>" ...
# → 201 Created

# REGISTRATION: cannot submit or verify
curl -X POST http://localhost:8000/api/workflow/usg/<report_id>/submit_for_verification/ -H "Authorization: Bearer <reg_token>"
# → 403 Access denied

# PERFORMANCE: can submit
curl -X POST http://localhost:8000/api/workflow/usg/<report_id>/submit_for_verification/ -H "Authorization: Bearer <perf_token>"
# → 200 OK

# PERFORMANCE: cannot finalize/publish
curl -X POST http://localhost:8000/api/workflow/usg/<report_id>/finalize/ -H "Authorization: Bearer <perf_token>"
# → 403 Access denied

# VERIFICATION: cannot edit
curl -X POST http://localhost:8000/api/workflow/usg/<report_id>/save_draft/ -H "Authorization: Bearer <ver_token>"
# → 403 Access denied

# VERIFICATION: can finalize
curl -X POST http://localhost:8000/api/workflow/usg/<report_id>/finalize/ -H "Authorization: Bearer <ver_token>"
# → 200 OK
```

### Automated test proof (command output)
```
python manage.py test apps.workflow.tests.Phase3RBACWorkflowTests
```

### Frontend proof (expected behavior)
- `reg_user` sees Registration only, and `/worklists/usg` shows Access denied.
- `perf_user` sees Report Entry only, and `/worklists/verification` shows Access denied.
- `ver_user` sees Verification only, and `/worklists/usg` shows Access denied.

## Files changed

- `backend/apps/workflow/api.py`
- `backend/apps/workflow/permissions.py`
- `backend/apps/workflow/transitions.py`
- `backend/apps/workflow/tests.py`
- `backend/apps/workflow/management/commands/seed_roles_phase3.py`
- `backend/rims_backend/urls.py`
- `frontend/src/ui/auth.tsx`
- `frontend/src/ui/App.tsx`
- `frontend/src/views/AccessDenied.tsx`
- `PHASE3_REPORT.md`

## Deferred items
- OPD-specific RBAC beyond current performance/verification desk checks (no additional desk roles introduced).
