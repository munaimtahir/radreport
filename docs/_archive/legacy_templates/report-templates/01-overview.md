# Report Templates Overview

## Goal
Provide a lightweight report template system with dynamic form capture that can be linked to services without disrupting legacy reporting flows.

## Key Concepts

### Models
- **ReportTemplate**: High-level template metadata (name/code/category/version) for dynamic reporting. Includes audit fields (created_by/updated_by) following repository patterns.
- **ReportTemplateField**: Flat list of fields (type, key, required, order) attached to a template. Supports: short_text, long_text, number, date, dropdown, checkbox, radio, heading, separator.
- **ReportTemplateFieldOption**: Dropdown/radio options for fields with label/value pairs.
- **ServiceReportTemplate**: Service-to-template link with a single default per service. Enforces one default template per service.
- **ReportTemplateReport**: Stored values for a service visit item with optional narrative text and status (draft/submitted/verified).

### Permissions
- **Admin-only**: Template CRUD, duplication, service linking
- **Reporting users**: Read template, save filled values (via worklist endpoints)

### Workflow Integration
- Templates are linked to services via `ServiceReportTemplate`
- When a worklist item is opened, the system checks for a default template
- If template exists → dynamic form renders
- If no template → legacy reporting flow continues unchanged

## Compatibility
- Legacy `Report` and `USGReport` flows remain unchanged
- Template reporting stores values separately and links to `ServiceVisitItem` for workflow alignment
- All changes are additive - no breaking changes to existing functionality
