# Template Governance v1 - Deployment Notes

**Date:** 2026-02-02
**Status:** ✅ Successfully Deployed

## What Was Deployed

### Backend

1. **Migration Applied:** `0007_template_governance`
   - Added governance fields to `ReportProfile`: `version`, `revision_of`, `status`, `is_frozen`, `activated_at/by`, `archived_at/by`
   - Created new model `TemplateAuditLog` for audit trail
   - Added unique constraint on `(code, version)`

2. **New API Endpoints:**
   - `POST /api/reporting/governance/{id}/clone/` - Clone template to new draft version
   - `POST /api/reporting/governance/{id}/activate/` - Activate draft (archives other active versions)
   - `POST /api/reporting/governance/{id}/freeze/` - Lock template
   - `POST /api/reporting/governance/{id}/unfreeze/` - Unlock template
   - `POST /api/reporting/governance/{id}/archive/` - Soft-delete template
   - `GET /api/reporting/governance/{id}/versions/` - List all versions
   - `GET /api/reporting/audit-logs/` - List audit logs with filtering
   - `GET /api/reporting/audit-logs/export-csv/` - Export logs to CSV

3. **Updated Endpoints:**
   - `ReportProfileViewSet.update()` - Now checks governance guards
   - `ReportProfileViewSet.destroy()` - Now checks governance guards
   - Added `status` filtering to profiles list

### Frontend

1. **Updated Components:**
   - `TemplatesList.tsx` - Shows version, status badges, governance actions
   - `TemplateEditor.tsx` - Shows read-only banner for frozen/in-use templates

2. **New Components:**
   - `AuditLogsPage.tsx` - Audit trail viewer with filtering and CSV export

3. **Updated Routes:**
   - Added `/settings/audit-logs` route in `App.tsx`
   - Added "Audit Logs" navigation link in sidebar

## Verification Results

### Step 1: Migrations ✅
```
$ docker compose exec backend python manage.py showmigrations reporting
...
[X] 0007_template_governance
```

### Step 2: Tests ✅
```
$ docker compose exec backend python manage.py test apps.reporting.tests.test_governance
Ran 16 tests in 8.763s
OK
```

**Tests Cover:**
- Clone copies parameters and options
- Activate deactivates other versions
- Activate requires confirmation
- Freeze blocks edits
- Unfreeze allows edits
- Archive blocked for active versions
- Archive requires confirmation
- Audit logs created for actions
- used_by_reports count accuracy
- Active with reports cannot be edited
- Delete blocked for active profiles
- Versions endpoint works
- Audit log API filtering
- Audit log CSV export

### Step 3: API Functionality ✅

**Clone Action:**
```json
POST /api/reporting/governance/{id}/clone/
Response: 201 Created
{
  "detail": "Cloned profile to version 2",
  "profile": { ... }
}
```

**Audit Log Entry:**
```json
{
  "id": "7f9f0cba-87b7-4486-8f5e-0af4962e08db",
  "actor": 1,
  "actor_username": "admin",
  "action": "clone",
  "entity_type": "report_profile",
  "metadata": {
    "code": "USG_KUB",
    "source_version": 1,
    "new_version": 2
  }
}
```

## Running Services

```
NAME                 STATUS           PORTS
rims_backend_prod    (healthy)        127.0.0.1:8015->8000/tcp
rims_frontend_prod   (healthy)        127.0.0.1:8081->80/tcp
rims_db_prod         (healthy)        5432/tcp
```

## Governance Workflow

1. **Active Template with Reports:** Cannot be directly edited
2. **To Make Changes:**
   - Clone → Creates draft v2
   - Edit → Make changes
   - Activate → v2 becomes active, v1 archived
3. **Freeze:** Optional lock to prevent accidental changes
4. **Archive:** Soft-delete for unused templates

## Files Changed

### Backend
- `apps/reporting/models.py` - Added governance fields
- `apps/reporting/serializers.py` - Extended serializers
- `apps/reporting/views.py` - Added governance guards
- `apps/reporting/governance_views.py` - NEW: Governance ViewSet
- `apps/reporting/urls.py` - Added new endpoints
- `apps/reporting/tests/test_governance.py` - NEW: Test suite
- `apps/reporting/migrations/0007_template_governance.py` - NEW: Migration

### Frontend
- `frontend/src/views/admin/TemplatesList.tsx` - Enhanced
- `frontend/src/views/admin/TemplateEditor.tsx` - Added governance banner
- `frontend/src/views/admin/AuditLogsPage.tsx` - NEW: Audit log viewer
- `frontend/src/ui/App.tsx` - Added route and nav link
- `frontend/src/theme.ts` - Added missing theme tokens
- `frontend/src/utils/download.ts` - Fixed type error
- `frontend/src/ui/components/ImportModal.tsx` - Fixed type error

### Documentation
- `RAD_TEMPLATE_STANDARDIZATION_REPORT.md` - Added Phase G section
