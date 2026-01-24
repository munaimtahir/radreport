# System Truth Map
**Last Updated:** January 25, 2026
**Status:** Clean Decontaminated State

This document serves as the absolute source of truth for the current implementation status of the system.

## Implemented Modules (Live & Verified)
These modules are actively used in the backend and frontend.

| Module | Status | Notes |
| os | :--- | :--- |
| **Patients** | ✅ Active | Registration, search, patient details. |
| **Consultants** | ✅ Active | Referral doctor management. |
| **Catalog** | ✅ Active | Service master (Modality -> Service). |
| **Studies** | ✅ Active | Visit/Order management. |
| **Workflow** | ✅ Active | Worklist, status transitions (Registered -> Completed -> Verified). |
| **Audit** | ✅ Active | System logging and audit trails. |
| **Receipts** | ✅ Active | Thermal receipt PDF generation (located in `backend/apps/workflow/pdf_engine`). |

## Not Implemented / Removed (Purged)
These features are **NOT** present in the codebase. Any documentation or code referring to them is stale.

- **Report Templates**: The `ReportTemplate`, `TemplateSchema`, `TemplateVersion` system has been completely removed.
- **Visual Report Editor**: The drag-and-drop or schema-based report editor is gone.
- **USG Template Import**: The Excel/JSON import for USG templates is removed.
- **Reporting Engine**: The document generation logic based on templates is removed.

## Workflow Status
1. **Registration**: Patient enters system.
2. **Worklist**: Studies appear in waiting list.
3. **Execution**: Technician marks as done (upload images/files).
4. **Verification**: Radiologist verifies usage (no report text yet).
5. **Receipts**: Payment and receipt generation works.

## Documentation Location
- **Active Docs**: `/docs` (root)
- **Archived/Legacy**: `/docs/_archive` (Consult for historical context only)
