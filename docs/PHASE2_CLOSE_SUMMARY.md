# Phase-2 Close: V2 PDF + Publish Snapshots + Narrative v0 — Summary Report

**Commit message:** `Close Phase-2: V2 PDF + publish snapshots + narrative v0`

---

## 1. Completed Work

### A. Backend

| Item | Status | Details |
|------|--------|---------|
| **ReportPublishSnapshotV2 model** | Done | `backend/apps/reporting/models.py`: `report_instance_v2`, `template_v2`, `values_json`, `narrative_json`, `pdf_file`, `content_hash`, `published_by`, `published_at`, `version`; indexes on `(report_instance_v2, published_at)` and `(content_hash)`. |
| **narrative_rules on TemplateV2** | Done | `ReportTemplateV2.narrative_rules` (JSONField); serializer and validation updated. |
| **Migrations** | Done | `0009_add_v2_publish_snapshot_and_narrative_rules.py` (model + narrative_rules); `0010_...` (index renames). |
| **Narrative engine v0** | Done | `backend/apps/reporting/services/narrative_v2.py`: `generate_narrative_v2(template_v2, values_json)`. Supports `sections` (title + lines) and `impression`; `{{field}}` interpolation; omit line if field missing/empty; boolean → Present/Absent. |
| **V2 PDF generator** | Done | `backend/apps/reporting/pdf_engine/report_pdf_v2.py`: `ReportPDFGeneratorV2` / `generate_report_pdf_v2`. Reuses V1 header/footer/patient table; body = narrative sections or values table. |
| **Dual-mode endpoints** | Done | **report-pdf:** V2 = on-the-fly from draft values + narrative; V1 unchanged. **publish:** V2 = create ReportPublishSnapshotV2 (narrative, PDF, content_hash); V1 unchanged. **published-pdf:** V2 = latest snapshot if no `?version=`; V1 = version required. **publish-history:** V2 and V1 both return history. **values:** V2 response includes `is_published`, `last_published_at`. |
| **V2 selection rule** | Done | `_get_v2_template()` uses mapping with `is_active=True`, `is_default=True`, `template__status="active"`. |

### B. Frontend

| Item | Status | Details |
|------|--------|---------|
| **V2 report entry (draft)** | Done | When `schema_version === "v2"`: **Preview PDF** and **Publish** buttons shown in draft (in addition to Save Draft). V1 draft unchanged (Submit Report only). |
| **API client** | Done | Existing `fetchReportPdf`, `publishReport`, `fetchPublishedPdf`, `getPublishHistory` work for V2 (dual-mode backend). No new client methods required. |
| **Published state** | Done | V2 values response includes `is_published` and `last_published_at`; publish history and “View Published PDF” work for V2. |

### C. Tests

| Item | Status | Details |
|------|--------|---------|
| **test_template_v2** | Pass | Existing template V2 tests. |
| **test_workitem_v2_routing** | Pass | Schema/values/save routing. |
| **test_workitem_v2_publish_pdf** | Pass | New file: schema v2, save draft, report-pdf (PDF response), publish (snapshot + hash), republish same hash, published-pdf. |
| **npm run build** | Pass | Frontend build succeeds. |

### D. Documentation

| Item | Status | Details |
|------|--------|---------|
| **Smoke doc (Phase 2)** | Done | `docs/PHASE1_REPORTING_V2_SMOKE.md` updated: narrative rules, Preview PDF, Publish, View Published PDF, republish, V1 unchanged, Phase 2 checklist, troubleshooting. API summary extended with report-pdf, publish, published-pdf, publish-history. |

---

## 2. Completion Checklist (from spec)

- [x] ReportPublishSnapshotV2 model + migration  
- [x] Narrative rules engine v0 implemented  
- [x] V2 PDF generator implemented  
- [x] WorkItem endpoints support V2 report-pdf + publish + published-pdf (dual-mode)  
- [x] Frontend shows Preview PDF / Publish / View Published PDF for V2 only  
- [x] All backend tests pass (template_v2, workitem_v2_routing, workitem_v2_publish_pdf)  
- [x] `npm run build` passes  
- [x] Smoke doc updated with Phase-2 steps  
- [x] Commit message: `Close Phase-2: V2 PDF + publish snapshots + narrative v0`  

---

## 3. Files Touched (summary)

**Backend**

- `backend/apps/reporting/models.py` — ReportPublishSnapshotV2, ReportTemplateV2.narrative_rules, ReportInstanceV2.is_published  
- `backend/apps/reporting/migrations/0009_...py` — V2 snapshot + narrative_rules  
- `backend/apps/reporting/migrations/0010_...py` — Index renames  
- `backend/apps/reporting/serializers.py` — narrative_rules in TemplateV2 serializer  
- `backend/apps/reporting/services/narrative_v2.py` — **new** narrative engine v0  
- `backend/apps/reporting/pdf_engine/report_pdf_v2.py` — **new** V2 PDF generator  
- `backend/apps/reporting/views.py` — logger, _get_v2_template(is_default=True), report_pdf/publish/published_pdf/publish_history/values dual-mode  
- `backend/apps/reporting/tests/test_workitem_v2_publish_pdf.py` — **new** V2 publish/PDF tests  

**Frontend**

- `frontend/src/views/ReportingPage.tsx` — V2 draft: Preview PDF + Publish buttons; V1 draft unchanged  

**Docs**

- `docs/PHASE1_REPORTING_V2_SMOKE.md` — Phase 2 steps, checklist, API summary, troubleshooting  
- `docs/PHASE2_CLOSE_SUMMARY.md` — **new** (this file)  

---

## 4. Constraints Verified

- **V1 unchanged:** V1 report-pdf, publish, published-pdf, submit/verify flows and ReportPublishSnapshot unchanged.  
- **V2 selection:** Only when mapping is `is_default=True` and `is_active=True` and template `status="active"`.  
- **Deterministic hash:** content_hash = SHA256 of `{ template_id, template_version, values_json, narrative_json }` (sort_keys=True); same input → same hash.  

---

## 5. Suggested Next Steps (optional)

- Enforce “verify before publish” for V2 if desired (currently V2 publish allowed from any status; permission = verifier/admin).  
- Add `narrative_rules` to Templates V2 UI (edit field) if not already present.  
- Run full regression on V1 reporting and workflow.  

Phase-2 implementation is complete and ready for commit with message: **`Close Phase-2: V2 PDF + publish snapshots + narrative v0`**.
