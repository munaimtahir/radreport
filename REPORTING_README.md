# Reporting Spine - Stage 0

## Philosophy
This reporting spine is built from first principles to replace legacy template systems. The core philosophy is **Parameter-Based Reporting** rather than **Text-Template Reporting**.

Instead of storing a blob of text (HTML/Markdown) as the report, we store discrete **parameters** (key-value pairs) defined by a **structured schema**. This allows:
- Deterministic data entry.
- Validation of values (numbers, options).
- Future analytics (e.g., "Show me all patients with Right Kidney Size > 12cm").
- Generating report narratives dynamically (Stage 2) rather than editing them manually.

## Architecture

### Backend Models (Django)
1.  **ReportProfile**: Defines the "Template" (e.g., "USG KUB").
2.  **ReportParameter**: Defines a field (e.g., "Right Kidney Size") with a type (Number, Text, Dropdown).
3.  **ServiceReportProfile**: Maps a Catalog Service (Charge) to a ReportProfile.
4.  **ReportInstance**: The actual report for a specific patient visit item.
5.  **ReportValue**: The specific value entered for a parameter.

### API (DRF)
- `GET /api/reporting/workitems/{id}/schema`: Returns the form definition.
- `GET /api/reporting/workitems/{id}/values`: Returns saved values.
- `POST /api/reporting/workitems/{id}/save`: Saves draft values.
- `POST /api/reporting/workitems/{id}/submit`: Lock report and mark as reported.

### Frontend
- Located at `/worklist/:id/report`.
- Renders the form dynamically based on the schema.
- Accessible via the Worklist (Dashboard / Department Worklists).

## Usage
1.  **Configuration**: Create `ReportProfile` and `ReportParameter`s in Admin. Link to `Service` via `ServiceReportProfile`.
2.  **Workflow**:
    - Patient is registered.
    - Technician/Doctor sees item in "My Worklist".
    - Clicks "Open".
    - Fills paramaters.
    - Clicks "Submit".
    - Item status moves to `PENDING_VERIFICATION` (Reported).

## Stage 2 (Next Steps)
- **Narrative Generation**: A logic layer to compile `ReportValues` into a readable text sentence/paragraph based on rules.
- **Verification UI**: Interface for Consultants to approve/publish the report.
- **PDF Generation**: Formatting the final output.
