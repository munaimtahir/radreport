# Verification

## Backend

### Migration
```bash
cd backend
python manage.py migrate
```
- Verify migration `0003_add_audit_fields_to_report_template` runs successfully
- Check that `ReportTemplate` model now has `created_by` and `updated_by` fields

### Server Boot
```bash
python manage.py runserver 0.0.0.0:8000
```
- Validate health endpoint: `curl http://localhost:8000/api/health/`
- Should return: `{"status":"ok","db":"ok",...}`

### API Testing
```bash
# Get auth token first
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'

# Test template endpoints (requires admin)
curl http://localhost:8000/api/report-templates/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test reporting endpoint (requires authenticated user)
curl http://localhost:8000/api/reporting/{item_id}/template/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Backend Tests
```bash
cd backend
python manage.py test apps.reporting.tests.ReportTemplateFlowTests
```
Expected:
- ✅ Template creation works
- ✅ Duplication works
- ✅ Service linking works
- ✅ Fetching template for workitem works
- ✅ Saving structured report values works

## Frontend

### Build
```bash
cd frontend
npm run build
```
- Should complete without errors
- Check `dist/` directory for built files

### Dev Server
```bash
npm run dev -- --host 0.0.0.0 --port 5173
```
- Server should start on `http://localhost:5173`
- Check browser console for errors

## UI Verification

### Admin Routes (Admin Users Only)
1. **Report Templates** (`/admin/report-templates`)
   - ✅ List templates
   - ✅ Create new template
   - ✅ Edit existing template
   - ✅ Add/remove/reorder fields
   - ✅ Configure field options (dropdown/radio)
   - ✅ Duplicate template
   - ✅ Activate/deactivate template

2. **Service Templates** (`/admin/service-templates`)
   - ✅ List services
   - ✅ Select service
   - ✅ View linked templates
   - ✅ Attach template to service
   - ✅ Set default template
   - ✅ Duplicate and attach
   - ✅ Deactivate link

### Reporting Routes (Performance Desk)
1. **USG Worklist** (`/worklists/usg`)
   - ✅ List pending visits
   - ✅ Select visit item
   - ✅ If template linked: Dynamic form renders
   - ✅ If no template: Legacy flow continues
   - ✅ Fill form fields (all types work)
   - ✅ Save draft (lenient validation)
   - ✅ Submit for verification (strict validation)
   - ✅ Required field indicators work
   - ✅ Error messages display correctly
   - ✅ Enter key does NOT auto-submit

### Legacy Compatibility
- ✅ Services without templates still work with legacy reporting
- ✅ Existing USG reports continue to function
- ✅ No breaking changes to existing workflows

## Integration Points Verified

### Template Resolution
- ✅ Service → `ServiceReportTemplate` lookup works
- ✅ Default template selection works (one per service)
- ✅ Fallback to legacy template when no report template exists

### Data Storage
- ✅ `ReportTemplateReport` values stored correctly
- ✅ Narrative text stored separately
- ✅ Status tracking (draft/submitted/verified) works
- ✅ One-to-one relationship with `ServiceVisitItem` enforced

### Permissions
- ✅ Admin-only actions require admin user
- ✅ Reporting users can read templates and save values
- ✅ Unauthorized access properly blocked

## Known Limitations / Future Enhancements
- Templates are flat (no sections/groups) - simpler for most use cases
- No PDF generation from templates yet (planned enhancement)
- No template versioning beyond version number field
- Templates can be duplicated but not versioned/historical
