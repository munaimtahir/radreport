# Report Templates Overview

## Goal
Provide a lightweight report template system with dynamic form capture that can be linked to services without disrupting legacy reporting flows.

## Key concepts
- **ReportTemplate**: High-level template metadata (name/code/category/version) for dynamic reporting.
- **ReportTemplateField**: Flat list of fields (type, key, required, order) attached to a template.
- **ReportTemplateFieldOption**: Dropdown/radio options for fields.
- **ServiceReportTemplate**: Service-to-template link with a single default per service.
- **ReportTemplateReport**: Stored values for a service visit item with optional narrative text and status.

## Compatibility
- Legacy `Report` and `USGReport` flows remain unchanged.
- Template reporting stores values separately and links to `ServiceVisitItem` for workflow alignment.
