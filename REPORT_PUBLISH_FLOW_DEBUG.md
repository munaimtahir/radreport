# Report Publish Flow - Debug Guide

## Overview

The report publish flow involves two separate models:
1. **ReportInstanceV2** - The working report instance (status: draft → submitted → verified)
2. **ReportPublishSnapshotV2** - Immutable snapshot created when publishing (one per publish)

## Flow

### 1. Report Lifecycle (ReportInstanceV2)
```
draft → submitted → verified → [published snapshot created]
```

### 2. Publish Process
When a verified report is published:
1. `publish()` endpoint is called
2. `_perform_publish_v2()` creates a **ReportPublishSnapshotV2**
3. PDF is generated and saved
4. ServiceVisitItem status changes to "PUBLISHED"
5. Audit log entry is created

## Key Models

### ReportInstanceV2
- **Purpose**: Working copy of the report
- **Status**: draft, submitted, verified, returned
- **Location**: Django Admin → Reporting → Report instance v2s
- **Relationship**: One-to-one with ServiceVisitItem

### ReportPublishSnapshotV2
- **Purpose**: Immutable published version
- **Created**: When `publish()` is called on a verified report
- **Location**: Django Admin → Reporting → Report publish snapshot v2s
- **Relationship**: Many-to-one with ReportInstanceV2 (can have multiple versions)

## Verification Steps

### 1. Check User Permissions
```python
# In Django shell
from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
groups = [g.name.lower() for g in user.groups.all()]
print(f"Groups: {groups}")
print(f"Has verification: {'verification' in groups or 'verification_desk' in groups}")
```

### 2. Check Report Status
```python
from apps.workflow.models import ServiceVisitItem
from apps.reporting.models import ReportInstanceV2

item = ServiceVisitItem.objects.get(id='your-item-id')
if hasattr(item, 'report_instance_v2'):
    instance = item.report_instance_v2
    print(f"Report Status: {instance.status}")
    print(f"Item Status: {item.status}")
    print(f"Can Verify: {instance.status == 'submitted'}")
    print(f"Can Publish: {instance.status == 'verified'}")
```

### 3. Check Publish Snapshots
```python
from apps.reporting.models import ReportPublishSnapshotV2

instance = ReportInstanceV2.objects.get(id='your-instance-id')
snapshots = instance.publish_snapshots_v2.all()
print(f"Publish Snapshots: {snapshots.count()}")
for snap in snapshots:
    print(f"  Version {snap.version}: {snap.published_at}")
    print(f"  PDF: {snap.pdf_file.name if snap.pdf_file else 'MISSING'}")
```

## Common Issues

### Issue 1: "Only verified reports can be published"
**Cause**: ReportInstanceV2 status is not "verified"
**Solution**: 
1. Check report status in Django Admin
2. Verify the report first (status must be "submitted" → "verified")
3. Then publish

### Issue 2: "Only verifiers can publish reports"
**Cause**: User doesn't have verification group
**Solution**:
1. Check user groups in Django Admin
2. Assign user to "Verification" group (or "verification_desk")
3. Log out and log back in

### Issue 3: Publish succeeds but no snapshot created
**Cause**: Database transaction failed or PDF generation error
**Solution**:
1. Check backend logs for errors
2. Verify MEDIA_ROOT is writable
3. Check disk space
4. Look for exceptions in logs

### Issue 4: Snapshot created but PDF missing
**Cause**: PDF file save failed
**Solution**:
1. Check MEDIA_ROOT permissions
2. Verify disk space
3. Check file path: `report_snapshots_v2/YYYY/MM/DD/Report_V2_*.pdf`

## Debug Script

Run the debug script to check everything:
```bash
python manage.py shell < debug_publish_flow.py
```

Or interactively:
```python
python manage.py shell
>>> exec(open('debug_publish_flow.py').read())
```

## API Endpoints

### Verify Report
```
POST /api/reporting/workitems/{item_id}/verify/
Body: { "notes": "optional notes" }
Requires: verification group
Changes: ReportInstanceV2.status = "verified"
```

### Publish Report
```
POST /api/reporting/workitems/{item_id}/publish/
Body: { "notes": "optional notes" }
Requires: verification group, ReportInstanceV2.status = "verified"
Creates: ReportPublishSnapshotV2
Changes: ServiceVisitItem.status = "PUBLISHED"
```

### Check Publish History
```
GET /api/reporting/workitems/{item_id}/publish-history/
Returns: List of all publish snapshots
```

## Logging

The publish flow now includes comprehensive logging:
- `publish_start` - Publish process started
- `publish_snapshot_created` - Snapshot created successfully
- `publish_item_status_updated` - Item status updated to PUBLISHED
- `publish_success` - Publish completed successfully
- `publish_error` - Error during publish (check logs for details)
- `publish_permission_denied` - User lacks permission
- `publish_invalid_status` - Report not in "verified" status

Check logs for these events to debug issues.

## Verification Checklist

- [ ] User has "Verification" or "verification_desk" group
- [ ] ReportInstanceV2 exists for the ServiceVisitItem
- [ ] ReportInstanceV2.status = "verified" (before publishing)
- [ ] Publish endpoint returns success with snapshot_id
- [ ] ReportPublishSnapshotV2 exists in database
- [ ] PDF file exists in MEDIA_ROOT
- [ ] ServiceVisitItem.status = "PUBLISHED" (after publishing)

## Testing

To test the full flow:
1. Create a report (draft)
2. Submit it (status → submitted)
3. Verify it (status → verified)
4. Publish it (creates snapshot, status → PUBLISHED)
5. Check Django Admin → Report publish snapshot v2s
6. Verify snapshot exists with PDF file
