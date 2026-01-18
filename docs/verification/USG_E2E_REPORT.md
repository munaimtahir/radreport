# USG End-to-End Reporting Verification

## Current state analysis

- **USG endpoints**: The API routes include `/api/usg/studies/`, `/api/usg/templates/`, `/api/usg/service-profiles/`, and `/api/usg/snapshots/` for USG lifecycle access and retrieval, confirming the USG API surface is registered in the backend router. 【F:backend/rims_backend/urls.py†L21-L63】
- **USG tables/models**: The USG subsystem defines `UsgTemplate`, `UsgServiceProfile`, `UsgStudy`, `UsgFieldValue`, and `UsgPublishedSnapshot` models, providing the storage required for template, study, values, and immutable snapshots. 【F:backend/apps/usg/models.py†L7-L204】
- **Service creation requires modality**: The `Service` model enforces a required `modality` foreign key and thus requires modality linkage for service creation. 【F:backend/apps/catalog/models.py†L6-L37】
- **Existing USG template/report system**: USG templates are loaded from JSON and stored in `UsgTemplate`, and the renderer/PDF generator build deterministic narrative output from stored template + values. 【F:backend/apps/usg/management/commands/load_usg_templates.py†L1-L55】【F:backend/apps/usg/renderer.py†L1-L137】【F:backend/apps/usg/pdf_generator.py†L1-L156】

## Steps executed

1. **Reviewed USG routing and models** to confirm study, template, and snapshot support in the backend. 【F:backend/rims_backend/urls.py†L21-L63】【F:backend/apps/usg/models.py†L7-L204】
2. **Added the USG Abdomen – Basic template** meeting the required sections and fields, with conditional rendering for dependent fields. 【F:backend/apps/usg/templates/usg_abdomen_basic.v1.json†L1-L205】
3. **Updated renderer conditional logic** to respect `show_when`/`visible_when` rules and keep NA fields out of output. 【F:backend/apps/usg/renderer.py†L1-L137】
4. **Updated USG publish flow** to persist immutable snapshots with frozen template schema and to store PDFs under MEDIA_ROOT with a saved path. 【F:backend/apps/usg/api.py†L1-L356】【F:backend/apps/usg/models.py†L151-L204】
5. **Added a seed command** to ensure USG modality and required services exist with the correct names/codes. 【F:backend/apps/catalog/management/commands/seed_usg_basic_services.py†L1-L39】
6. **Aligned service profiles** to the new USG Abdomen – Basic template for Abdomen, Pelvis, and KUB. 【F:backend/apps/usg/management/commands/seed_usg_service_profiles.py†L1-L62】

## Verification evidence

- **USG study lifecycle endpoints** are registered and publish produces snapshots, while PDF retrieval prefers the stored file under MEDIA_ROOT. 【F:backend/rims_backend/urls.py†L21-L63】【F:backend/apps/usg/api.py†L1-L356】
- **Snapshot immutability** is enforced by published-study guards and stored snapshots include the frozen template schema plus field values. 【F:backend/apps/usg/api.py†L1-L356】【F:backend/apps/usg/models.py†L151-L204】
- **Conditional/NA behavior** is enforced in the renderer to omit NA or unmet conditional fields in narrative output. 【F:backend/apps/usg/renderer.py†L1-L137】

## PASS / FAIL summary

- **Current verification status**: **FAIL (runtime verification not executed)**
  - No live API or database-backed smoke run was executed in this environment.

## Known limitations

- **Runtime verification not executed**: The environment did not run the live backend or database, so API calls, PDF generation, and snapshot retrieval were not exercised end-to-end here. Follow the steps below in an environment with the services running.

---

## Required end-to-end verification steps (to run in a live environment)

> NOTE: Run these commands against the deployed environment and record outputs here.

### Phase 0 — Context confirmation

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<host>/api/usg/studies/
```

- Confirm USG tables exist via Django admin or database inspection.
- Confirm USG service creation requires a modality and succeeds.

### Phase 1 — Data seeding

```bash
python manage.py seed_usg_basic_services
python manage.py load_usg_templates
python manage.py seed_usg_service_profiles
```

### Phase 2 — Study lifecycle

```bash
# 1) Create patient + visit + add Ultrasound Abdomen (registration workflow)
# 2) Create study
curl -X POST http://<host>/api/usg/studies/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"patient": "<patient_id>", "visit": "<visit_id>", "service_code": "USG_ABDOMEN"}'

# 3) Save draft values (with some NA)
curl -X PATCH http://<host>/api/usg/studies/<study_id>/values/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"values": [{"field_key": "liver_focal_lesion", "value_json": "no", "is_not_applicable": false}, {"field_key": "pancreas_notes", "value_json": null, "is_not_applicable": true}]}'

# 4) Publish
curl -X POST http://<host>/api/usg/studies/<study_id>/publish/ \
  -H "Authorization: Bearer <token>"

# 5) Attempt edit (should fail with "Published study is locked")
curl -X PATCH http://<host>/api/usg/studies/<study_id>/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "draft"}'

# 6) Download PDF
curl -o usg_report.pdf -L http://<host>/api/usg/studies/<study_id>/pdf/ \
  -H "Authorization: Bearer <token>"
```

### Phase 3 — Template immutability validation

1. Update the USG Abdomen – Basic template (new version), reload templates.
2. Create a new study and publish.
3. Confirm old snapshot JSON/PDF remains unchanged and new study uses updated template.

---

## Notes

- Update this document with actual HTTP response codes, snapshot IDs, and PDF hashes once the steps above are executed in the target environment.
