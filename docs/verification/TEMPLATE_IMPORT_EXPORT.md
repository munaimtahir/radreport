# Template Import / Export Engine - Verification & System State

## Current System State (Phase 0 Discovery)

### Existing Models
Analysis of `backend/apps/templates/models.py` reveals two parallel template systems:

1.  **Core Template System (`Template` + `TemplateVersion`)**
    *   **Structure**: `Template` (Head) -> `TemplateVersion` (History).
    *   **Versioning**: `TemplateVersion` stores a frozen `schema` (JSON).
    *   **Usage**: Linked to `Report` (via `TemplateVersion`) and `Service` (via `Template`).
    *   **Current State**: 1 row in DB.
    *   **Gap Analysis**: Missing `code` field required for TemplatePackage v1.

2.  **Report Template System (`ReportTemplate`)**
    *   **Structure**: `ReportTemplate` -> `ReportTemplateField`.
    *   **Usage**: Linked to `ReportTemplateReport` (appears unused or secondary).
    *   **Current State**: 1 row in DB.

### Critical Decision
We will utilize the **Core Template System (`Template` + `TemplateVersion`)** as the target for the Import Engine because:
*   It supports versioned schema snapshots natively.
*   It is linked to the primary `Report` model.
*   It aligns with the "immutable published reports" requirement.

### Verification Matrix
| ID | Requirement | Status | Note |
|----|-------------|--------|------|
| 1.0 | Validate invalid JSON | Pending | |
| 2.0 | Import valid template | Pending | |
| 3.0 | Import update (v2) | Pending | |
| 4.0 | Export v1 | Pending | |
| 5.0 | Round-trip integrity | Pending | |
| 6.0 | Published report safety | Pending | |
