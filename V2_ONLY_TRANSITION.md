# Reporting V2 Only Transition

## Truth Map

| Component | Status | Details |
|-----------|--------|---------|
| **V1 Models** | **Removed** | `ReportProfile`, `ReportParameter`, etc. are removed from `backend/apps/reporting/models.py`. |
| **V1 Views** | **Removed** | `ReportProfileViewSet`, `ReportParameterViewSet` are absent from `urls.py` and `views.py`. |
| **V1 Fallback** | **Removed** | `ReportWorkItemViewSet` now strictly checks for V2 mapping. |
| **V2 Models** | **Active** | `ReportTemplateV2`, `ServiceReportTemplateV2`, `ReportInstanceV2`, `ReportPublishSnapshotV2` are the source of truth. |
| **V2 Views** | **Active** | `ReportTemplateV2ViewSet`, `ServiceReportTemplateV2ViewSet`, `ReportWorkItemViewSet` (V2 logic). |

## V2 Endpoints (Active)

*   `GET /api/reporting/workitems/{id}/schema/` - Returns V2 schema (or 409 Conflict if missing).
*   `GET /api/reporting/workitems/{id}/values/` - Returns V2 values.
*   `POST /api/reporting/workitems/{id}/save/` - Saves V2 values.
*   `POST /api/reporting/workitems/{id}/submit/` - Submits V2 report.
*   `POST /api/reporting/workitems/{id}/verify/` - Verifies V2 report.
*   `POST /api/reporting/workitems/{id}/publish/` - Publishes V2 report.
*   `GET /api/reporting/workitems/{id}/report-pdf/` - Generates PDF for V2.
*   `GET /api/reporting/templates-v2/` - CRUD for V2 Templates.
*   `GET /api/reporting/service-templates-v2/` - CRUD for Service Mappings.
*   `GET /api/reporting/block-library/` - CRUD for UI/Narrative blocks.

## V1 Endpoints (Disabled/Gone)

*   `/api/reporting/profiles/*` - 404 Not Found
*   `/api/reporting/parameters/*` - 404 Not Found
*   `/api/reporting/service-profiles/*` - 404 Not Found

## Import Command

New management command available for importing V2 templates and mappings.

**Usage:**

```bash
docker compose exec backend python manage.py import_templates_v2 \
  --templates /app/baseline_packs_v2/templates_v2.json \
  --mappings /app/baseline_packs_v2/service_template_v2_links.csv \
  --activate
```

**Flags:**
*   `--dry-run`: Validate inputs without saving.
*   `--strict`: Fail if referenced services/templates are missing.
*   `--activate`: Automatically activate the imported template.
*   `--deactivate-missing`: Deactivate mappings not present in the input file.

## Operator Checklist: Onboarding a New Service

1.  **Define Template:** Create a JSON file (or entry in `templates_v2.json`) with `json_schema`, `ui_schema`, and `narrative_rules`.
2.  **Define Mapping:** Add row to `service_template_v2_links.csv` mapping `service_code` -> `template_code`.
3.  **Run Import:**
    ```bash
    docker compose exec backend python manage.py import_templates_v2 ... --activate
    ```
4.  **Verify:** Open the Reporting Worklist, click "Report" on the service, and ensure the new V2 UI loads.

