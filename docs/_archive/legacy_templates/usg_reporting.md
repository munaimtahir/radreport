# USG Reporting Subsystem Documentation

## Overview

The USG (Ultrasound) reporting subsystem implements structured ultrasound reports with:
- Template-based structured data entry
- Draft → Verify → Publish workflow
- Immutable published snapshots
- Google Drive PDF storage
- Deterministic narrative rendering

## Key Principles

### 1. Immutability
Published reports are **forever locked**:
- Cannot edit study metadata
- Cannot modify field values
- Cannot delete published studies
- Enforced at model, serializer, and API levels

### 2. Snapshot Architecture
Every published report stores:
- `published_json_snapshot`: Frozen field values with NA flags
- `published_text_snapshot`: Final narrative text as issued
- `pdf_drive_file_id`: Google Drive permanent record
- Template code + version + renderer version

### 3. Deterministic Rendering
- Renderer version: `usg_renderer_v1`
- PDF layout version: `usg_pdf_layout_v1`
- Same inputs always produce same output
- Future template changes don't affect past reports

### 4. Not Applicable Logic
Every field supports `is_not_applicable=true`:
- Field excluded from rendering
- If section has no printable fields → section excluded
- Clean narrative without clutter

## Data Models

### UsgTemplate
Stores template schemas with sections and fields.
- Locked templates cannot be modified
- Version tracking for schema changes
- Stable field keys (never rename)

### UsgServiceProfile (optional)
Maps service codes to templates with visibility rules.
- Hidden sections for specific services
- Forced NA fields

### UsgStudy
One instance per patient visit exam.
- Links to Patient and Visit (RIMS core)
- Status: draft → verified → published
- Immutable when published

### UsgFieldValue
Structured truth for field values.
- Supports multi-select, text, numeric, choice
- `is_not_applicable` flag
- Cannot modify if study published

### UsgPublishedSnapshot
Immutable published report record.
- One-to-one with UsgStudy
- Stores JSON + narrative + PDF metadata
- Never deletable

## Workflow

### 1. Create Draft Study
```
POST /api/usg/studies/
{
    "patient": "<patient_id>",
    "visit": "<visit_id>",
    "service_code": "USG_ABDOMEN",
    "template": "<template_id>"
}
```

### 2. Fill Field Values
```
PUT /api/usg/studies/{id}/values/
{
    "values": [
        {
            "field_key": "liver_size",
            "value_json": "normal",
            "is_not_applicable": false
        },
        {
            "field_key": "gb_calculi",
            "value_json": null,
            "is_not_applicable": true
        }
    ]
}
```

### 3. Preview Narrative (Draft Only)
```
POST /api/usg/studies/{id}/render/
```

Returns rendered narrative for preview.

### 4. Publish
```
POST /api/usg/studies/{id}/publish/
```

Atomically:
1. Freezes field values into snapshot
2. Generates narrative using renderer v1
3. Creates PDF using layout v1
4. Uploads to Google Drive
5. Creates UsgPublishedSnapshot
6. Locks study (status=published)

### 5. Retrieve PDF
```
GET /api/usg/studies/{id}/pdf/
```

Returns PDF:
- From Drive if available
- Regenerates from `published_text_snapshot` if missing
- Re-uploads to Drive with audit note

### 6. List Visit Reports
```
GET /api/visits/{visit_id}/usg-reports/
```

Returns all USG studies for a visit.

## Template Schema Format

See `apps/usg/templates/usg_abdomen_base.v1.json` for full example.

Key structure:
```json
{
  "code": "USG_ABDOMEN_BASE",
  "name": "USG Abdomen – Base",
  "category": "abdomen",
  "version": 1,
  "sections": [
    {
      "section_key": "liver",
      "title": "Liver",
      "include_toggle": true,
      "fields": [
        {
          "field_key": "liver_size",
          "label": "Liver Size",
          "type": "single_choice",
          "supports_not_applicable": true,
          "options": [
            {"label": "Normal", "value": "normal"},
            {"label": "Enlarged", "value": "enlarged"}
          ]
        }
      ]
    }
  ]
}
```

### Field Types
- `text`: Free text input
- `number`: Numeric value
- `single_choice`: Select one option
- `multi_choice`: Select multiple options

## Google Drive Integration

### Setup
Set environment variables:
```bash
# Option 1: JSON string
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Option 2: File path
GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH=/path/to/credentials.json

# Parent folder ID
GOOGLE_DRIVE_USG_FOLDER_ID=<drive_folder_id>
```

### Folder Structure
```
Ultrasound Reports/
  2026/
    01/
      USG_USG_ABDOMEN_MR123_VN20260117_uuid.pdf
      USG_USG_KUB_MR456_VN20260117_uuid.pdf
    02/
      ...
  2027/
    ...
```

### Dependencies
Install Google Drive API client:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Template Versioning

When updating templates:
1. Create new template with version = old_version + 1
2. New studies use new template
3. Published reports always reference their template version
4. Old reports never affected

## Management Commands

### Load Templates
```bash
python manage.py load_usg_templates
```

Loads all `.json` files from `apps/usg/templates/`.

## API Permissions

Current: `IsAuthenticated` for all endpoints.

Recommended production roles:
- **Reporter**: Can create/edit drafts
- **Verifier**: Can verify reports
- **Publisher**: Can publish reports (creates immutable snapshot)
- **Viewer**: Can view published reports only

## Safety Guarantees

✅ Published reports cannot be edited  
✅ Published reports cannot be deleted  
✅ Template changes don't affect past reports  
✅ PDF always regenerable from `published_text_snapshot`  
✅ Field values frozen at publish time  
✅ Renderer version tracked for reproducibility  

## Testing Checklist

- [ ] Create draft study
- [ ] Fill field values (some NA)
- [ ] Preview narrative (should omit NA fields)
- [ ] Publish study
- [ ] Try editing published study (must fail)
- [ ] Retrieve PDF
- [ ] Simulate missing Drive PDF (delete from Drive)
- [ ] Retrieve PDF again (should regenerate + re-upload)
- [ ] List reports from visit endpoint
- [ ] Update template (bump version)
- [ ] Verify old published report unchanged

## Migration Notes

Run migrations:
```bash
python manage.py makemigrations usg
python manage.py migrate usg
```

Load base template:
```bash
python manage.py load_usg_templates
```

## Future Enhancements

- Role-based permissions (reporter/verifier/publisher)
- Digital signatures on PDF
- Template builder UI
- Bulk import of templates
- Report comparison (before/after)
- DICOM integration
- HL7 FHIR export
