# DB Cleanup Plan: Purging Deleted Apps
**Date:** 2026-01-24
**Apps to purge:** `templates`, `usg`, `reporting`
**Constrains:** Preserve `patients`, `studies`, `workflow`, `consultants`, `audit`, `auth`, `catalog`.

## Overview
This plan details the removal of database tables associated with the deleted Django applications. 
A full database backup has been performed prior to this operation.

## Tables to Drop
The following tables are identified as belonging to the deleted apps and will be dropped with `CASCADE`.
The `CASCADE` option is necessary to remove Foreign Key constraints from preserved tables (`catalog_service`, `workflow_usgreport`) that reference these tables.

### App: reporting
- `reporting_report`
- `reporting_reporttemplatereport`

### App: templates
- `templates_fieldoption`
- `templates_reporttemplate`
- `templates_reporttemplatefield`
- `templates_reporttemplatefieldoption`
- `templates_servicereporttemplate`
- `templates_template` (Referenced by `catalog_service.default_template_id`)
- `templates_templatefield`
- `templates_templatesection`
- `templates_templateversion` (Referenced by `workflow_usgreport.template_version_id`)

### App: usg
- `usg_usgfieldvalue`
- `usg_usgpublishedsnapshot`
- `usg_usgserviceprofile`
- `usg_usgstudy`
- `usg_usgtemplate`

## Preserved Tables (Notable Mentions)
- `workflow_usgreport`: **KEPT**. This is the active report table in the `workflow` app. It references `templates_templateversion`, so the FK constraint will be dropped, but the table and data remain.
- `catalog_service`: **KEPT**. References `templates_template`, FK constraint will be dropped.

## Verification Steps
1. Execute SQL script.
2. Verify tables are gone.
3. Clean `django_migrations` table.
4. Run `python manage.py check`.
5. Run generic smoke tests (Patient Registration, etc).

## Risks
- **Data Loss**: Legacy report data in `usg_usgstudy` or `reporting_report` will be lost. This is intended as per "Deleted backend apps" directive.
- **Dangling Columns**: `catalog_service.default_template_id` and `workflow_usgreport.template_version_id` will exist but populated with IDs pointing to nowhere. This is acceptable for a DB cleanup task of this scope. Codebase removal of fields ensures they are ignored.
