# Phase 1 & 2 Reporting V2 — Manual Smoke Steps

This document describes manual smoke steps to verify Reporting V2 works end-to-end in dual mode: services with an active + default V2 mapping use SchemaFormV2 and JSON values; all other services continue to use V1 reporting unchanged.

**Phase 2 additions:** V2 PDF generation, Publish snapshots, and basic Narrative rules execution.

## Prerequisites

- Backend and frontend running (e.g. `docker compose up` or local dev servers).
- Log in as an admin user.

---

## 1. Seed baseline pack (if needed)

Ensure at least one service exists for mapping:

- Go to **Settings → Baseline Packs**, or
- Use existing services from **Settings → Services**.

If you use a baseline pack, apply it so that services (e.g. USG Abdomen, USG KUB) exist.

---

## 2. Create a TemplateV2

1. Go to **Settings → Templates V2** (route: `/settings/templates-v2`).
2. Click **Create** (or equivalent).
3. Fill:
   - **Code**: e.g. `USG_ABD_V2`
   - **Name**: e.g. `USG Abdomen V2`
   - **Modality**: e.g. `USG`
   - **JSON Schema**: paste a valid JSON schema (see example below).
   - **UI Schema**: paste a valid JSON object (see example below); can be `{}` for minimal test.
4. Parse/validate JSON before submit; fix any parse errors shown.
5. Save. Template should be in **Draft** status.

### Example `json_schema`

```json
{
  "type": "object",
  "required": ["liver_size_cm"],
  "properties": {
    "liver_size_cm": { "type": "number", "title": "Liver size (cm)" },
    "liver_echo": { "type": "string", "title": "Liver echotexture", "enum": ["Normal", "Coarse", "Fatty"] },
    "gb_stones": { "type": "boolean", "title": "Gall bladder stones" },
    "comments": { "type": "string", "title": "Comments" }
  }
}
```

### Example `ui_schema`

```json
{
  "groups": [
    { "title": "Liver", "fields": ["liver_size_cm", "liver_echo"] },
    { "title": "Gall Bladder", "fields": ["gb_stones"] },
    { "title": "Notes", "fields": ["comments"], "widgets": { "comments": "textarea" } }
  ]
}
```

*(The UI also supports `sections` instead of `groups` with the same structure.)*

---

## 3. Activate the template

1. On the Templates V2 list, find the new template.
2. Click **Activate**.
3. If you get **409 Conflict** (another active template with same code/modality):
   - Use **Force activate** (retry with `?force=1`); this archives the conflicting active template.
4. After success, template status should be **Active**.

---

## 4. Create service mapping and set default

1. In **Templates V2** (or the service mapping section), create a mapping:
   - **Service**: select a service (e.g. the one you use for reporting).
   - **Template**: select the TemplateV2 you just activated.
   - **Is active**: checked.
   - **Is default**: checked (required for V2 to apply).
2. Save the mapping.
3. If there is a **Set default** button for that mapping, use it to ensure this mapping is the default for the service (it clears other defaults for that service). Rule: if user sets default, the mapping should be active.

---

## 5. Open/create a WorkItem for that service (V2 path)

1. Go to **Reporting worklist** and pick a visit that has a service item for the service you mapped (or create a new visit with that service).
2. Open the **report entry** for that work item (e.g. “Enter report” or similar).
3. **Confirm:**
   - The schema endpoint returns **`schema_version: "v2"`** (you can check in network tab: `GET .../workitems/{id}/schema/`).
   - The form renders **SchemaFormV2** (JSON-schema-driven fields: number, enum dropdown, boolean, string; groups/sections and optional textarea for `comments`).
4. **Save draft:**
   - Fill a few fields and click **Save draft**.
   - Request should be `POST .../workitems/{id}/save/` with body `{ "schema_version": "v2", "values_json": { ... } }`.
   - UI shows success (e.g. “Draft saved successfully”).
5. **Reload values:**
   - Refresh the page or re-open the same report.
   - **Confirm:** `GET .../workitems/{id}/values/` returns **`schema_version: "v2"`** and **`values_json`** with the data you saved; form shows the same values.

---

## 6. Open a WorkItem for a non‑V2 service (V1 unchanged)

1. Pick a service that has **no** active + default V2 mapping (e.g. only V1 profile, or no V2 mapping at all).
2. Open the report entry for a work item of that service.
3. **Confirm:**
   - Schema response includes **`schema_version: "v1"`** and the usual V1 structure (e.g. `parameters`).
   - The **V1 parameter form** is shown (sections, parameter types, etc.).
   - Save draft uses the existing V1 payload (`values` list).
   - Submit/verify/publish/PDF remain V1; no change in behavior.

---

## 7. Quick checklist

- [ ] Baseline pack or services exist.
- [ ] TemplateV2 created with valid `json_schema` and `ui_schema` (e.g. examples above).
- [ ] Template activated; conflict handled with force if needed.
- [ ] Service mapping created with **is_active** and **is_default**; default set for that service.
- [ ] WorkItem for V2-mapped service: schema returns v2, form is SchemaFormV2, draft save/load works.
- [ ] WorkItem for non‑V2 service: schema returns v1, V1 form and save unchanged.

---

## API summary (for reference)

- **Schema:** `GET /api/reporting/workitems/{id}/schema/`  
  - V2: `{ schema_version: "v2", template, json_schema, ui_schema }`  
  - V1: `{ schema_version: "v1", ...profile schema... }`
- **Values:** `GET /api/reporting/workitems/{id}/values/`  
  - V2: `{ schema_version: "v2", values_json, status, last_saved_at, is_published, last_published_at }` (creates ReportInstanceV2 if missing)  
  - V1: `{ schema_version: "v1", status, values, ... }`
- **Report PDF (preview):** `GET /api/reporting/workitems/{id}/report-pdf/` — V2: on-the-fly from draft; V1: existing.
- **Publish:** `POST /api/reporting/workitems/{id}/publish/` — V2: creates ReportPublishSnapshotV2; V1: existing.
- **Published PDF:** `GET /api/reporting/workitems/{id}/published-pdf/` (optional `?version=N`) — V2: latest if no version; V1: version required.
- **Publish history:** `GET /api/reporting/workitems/{id}/publish-history/` — dual-mode (V1/V2).
- **Save:** `POST /api/reporting/workitems/{id}/save/`  
  - V2: `{ schema_version: "v2", values_json }`  
  - V1: `{ values: [ { parameter_id, value } ] }`

V2 is used only when the service has a mapping with **is_active=True**, **is_default=True**, and **template status="active"**.

---

## Phase 2: V2 PDF Generation + Publish + Narrative

Phase 2 adds V2 PDF generation, publish snapshots, and basic narrative rules execution.

### 8. Add narrative rules to TemplateV2 (optional)

1. Go to **Settings → Templates V2** and edit your V2 template.
2. Add **Narrative Rules** (JSON format):

```json
{
  "sections": [
    {
      "title": "Liver",
      "lines": [
        "Liver size: {{liver_size_cm}} cm",
        "Echotexture: {{liver_echo}}"
      ]
    },
    {
      "title": "Gall Bladder",
      "lines": ["Stones: {{gb_stones}}"]
    }
  ],
  "impression": ["{{comments}}"]
}
```

3. Save the template.
4. **Note:** If no narrative rules are provided, the PDF will show values as a table instead.

### 9. Preview PDF for V2 report (draft)

1. Open a V2 work item report (from step 5).
2. Fill in some values and click **Save Draft**.
3. Click **Preview PDF** button.
4. **Confirm:**
   - PDF opens in a new tab.
   - PDF shows patient demographics, service name, and report values.
   - If narrative rules exist, PDF shows narrative sections; otherwise shows values table.
   - PDF has facility branding (logo, name, address from ReportingOrganizationConfig).

### 10. Publish V2 report

1. With the same V2 work item open, click **Publish** button.
2. **Confirm:**
   - Success message appears.
   - Response includes: `status: "published"`, `version: 1`, `content_hash`, `snapshot_id`.
3. **Backend verification:**
   - Check that `ReportPublishSnapshotV2` record was created with:
     - `version = 1`
     - `values_json` = saved values
     - `narrative_json` = generated narrative (if rules exist)
     - `pdf_file` = stored PDF artifact
     - `content_hash` = SHA256 hash (64 chars)

### 11. View published PDF

1. After publishing, click **View Published PDF** (or use endpoint `GET /api/reporting/workitems/{id}/published-pdf/`).
2. **Confirm:**
   - PDF opens showing the published snapshot.
   - PDF matches the values that were saved at publish time.
   - PDF filename includes version number (e.g., `Report_V2_VISIT001_v1.pdf`).

### 12. Republish with same values

1. Click **Publish** again without changing values.
2. **Confirm:**
   - New snapshot created with `version = 2`.
   - `content_hash` is the same as version 1 (same values = same hash).
   - Both snapshots are stored independently.

### 13. Verify V1 publish/PDF still works unchanged

1. Open a work item for a service that uses **V1** (no V2 mapping).
2. Fill values, submit, verify, and publish.
3. **Confirm:**
   - V1 publish flow works as before.
   - V1 PDF generation works as before.
   - V1 `ReportPublishSnapshot` (not V2) is created.
   - No interference with V2 functionality.

---

## Phase 2 Checklist

- [ ] Narrative rules can be added to TemplateV2 (optional).
- [ ] Preview PDF works for V2 draft reports.
- [ ] PDF shows patient demographics, values, and narrative (if rules exist).
- [ ] Publish creates `ReportPublishSnapshotV2` with immutable values, narrative, PDF, and hash.
- [ ] View Published PDF retrieves snapshot PDF.
- [ ] Republish with same values produces same content_hash but new version.
- [ ] V1 publish/PDF flows remain unchanged and functional.

---

## Troubleshooting

### PDF generation fails

- Check that `ReportingOrganizationConfig` exists with valid branding.
- Check that logo file exists at the configured path.
- Check backend logs for PDF generation errors.

### Publish fails with 409

- Ensure user has verifier permissions (or is admin).
- Check that ReportInstanceV2 exists for the work item.

### Narrative not showing in PDF

- Verify `narrative_rules` is set in TemplateV2.
- Check that field names in `{{field}}` placeholders match `values_json` keys.
- If a field is missing/empty, that line will be omitted (by design).

### Content hash mismatch on republish

- This is expected if values or narrative rules changed between publishes.
- Same values + same template = same hash (deterministic).
