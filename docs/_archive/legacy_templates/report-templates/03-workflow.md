# Report Templates Workflow

## Admin Workflow

### Creating Templates
1. Navigate to **Admin → Report Templates** (admin-only)
2. Click "Create Template"
3. Fill in template metadata:
   - Name (required)
   - Code (optional, unique identifier)
   - Category (optional, for organization)
   - Description (optional)
   - Version (default: 1)
   - Active status
4. Add fields:
   - Click "Add Field"
   - Configure each field:
     - Label, Key (unique per template)
     - Field Type (short_text, long_text, number, date, dropdown, checkbox, radio, heading, separator)
     - Required flag
     - Help text, placeholder, default value
     - For dropdown/radio: add options with label/value pairs
   - Reorder fields using up/down arrows
5. Save template (creates template, then updates fields via bulk PUT endpoint)

### Duplicating Templates
- Click "Duplicate" on any template
- Creates a copy with "(Copy)" suffix
- All fields and options are cloned
- Useful for creating variations of existing templates

### Linking Templates to Services
1. Navigate to **Admin → Service Templates** (admin-only)
2. Select a service from the list
3. Choose a template from dropdown
4. Optionally set as default (only one default per service)
5. Click "Attach" or "Duplicate & Attach"
6. Multiple templates can be linked, but only one can be default

## Reporting Workflow

### Using Templates in Worklist
1. Open a worklist item (e.g., USG Worklist)
2. System automatically checks for default template linked to the service
3. If template exists:
   - Dynamic form renders with all template fields
   - Pre-fills with existing saved values or defaults
   - Shows required field indicators
   - Supports all field types (text, number, date, dropdown, checkbox, radio, etc.)
4. Fill in form fields
5. Optional: Add narrative text
6. Save Draft:
   - Validates non-required fields only
   - Stores values via `/api/reporting/{workitem_id}/save-template-report/`
   - Sets status to "draft"
   - Item transitions to "IN_PROGRESS" if previously "REGISTERED"
7. Submit for Verification:
   - Validates ALL required fields
   - Returns errors if validation fails
   - Stores values and sets status to "submitted"
   - Item transitions to "PENDING_VERIFICATION"
   - Work item is locked for further editing (until returned)

### Field Validation
- **Draft save**: Lenient - only validates data types and option values
- **Submit**: Strict - enforces all required fields
- Validation errors returned as `{ errors: { field_key: "error message" } }`

### Keyboard UX
- Enter key is prevented from auto-submitting forms
- Explicit "Save" and "Submit" buttons only
- Prevents accidental submissions

## Legacy Compatibility

### No Template Scenario
- If no report template exists for a service, the existing reporting flow continues unchanged
- Legacy template schema rendering (from `Template`/`TemplateVersion`) still works
- Free-text reporting still works
- USG report workflow remains unchanged

### Template vs Legacy
- Templates are checked first via `ServiceReportTemplate` lookup
- If no template link exists, falls back to:
  1. Legacy `Template`/`TemplateVersion` schema (via `Service.default_template`)
  2. Free-text USG report entry
- Both systems can coexist - templates are additive only
