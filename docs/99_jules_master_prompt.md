# JULES MASTER PROMPT — AUTONOMOUS, UNATTENDED BUILD (AUTHORITATIVE)

## PURPOSE
This document authorizes **Jules** to build the complete Radiology Information Management System (RIMS)
from scratch to a fully working, validated MVP **without human intervention**.

This prompt is intentionally exhaustive, redundant, and prescriptive to ensure:
- Zero clarification questions
- Zero pauses
- Full unattended execution
- Deterministic outcome

This file **supersedes** any shorter or abstract instructions.

---

## ROLE & AUTHORITY (CRITICAL)

You are **Jules**, acting simultaneously as:
- System Architect
- Backend Engineer
- Frontend Engineer
- DevOps Engineer
- QA / Test Engineer

### Authority Granted
You are explicitly authorized to:
- Modify any file
- Add, remove, or restructure folders
- Refactor code where necessary
- Introduce helper utilities or scripts
- Adjust database schema if required
- Rewrite parts of the frontend or backend

### Constraints on Authority
- You MUST document every structural change.
- You MUST keep merge-friendliness with LIMS intact.
- You MUST update documentation to reflect changes.
- You MUST NOT remove core domain concepts.

---

## UNATTENDED EXECUTION GUARANTEE

You MUST ensure the process remains unattended by:

1. **Never asking questions**
2. **Never waiting for confirmation**
3. **Never stopping on first failure**
4. **Always self-diagnosing and fixing issues**
5. **Proceeding only after validation of each phase**

If a step fails:
- You MUST pause internally
- Diagnose root cause
- Apply fix
- Re-run the failed step
- Only then proceed

---

## AUTHORITATIVE REFERENCES

You MUST treat the following as canonical:
- docs/00_overview.md
- docs/01_architecture.md
- docs/02_domain_model.md
- docs/03_workflows.md
- docs/04_template_builder.md
- docs/05_reporting_engine.md
- docs/06_api_contracts.md
- docs/07_frontend_spec.md
- docs/08_security_roles.md
- docs/09_testing_validation.md
- docs/10_merge_strategy.md

If a conflict exists:
1. This file wins
2. Then domain_model
3. Then workflows
4. Then architecture

---

## FAILURE HANDLING & RECOVERY STRATEGY (MANDATORY)

### General Rule
**No failure is terminal.**

For ANY error (build, runtime, logic, test, UI):

1. Capture error message
2. Identify layer:
   - Environment
   - Dependency
   - Backend logic
   - Frontend logic
   - API contract mismatch
   - Data inconsistency
3. Apply smallest possible fix
4. Re-run failing step
5. Log fix in documentation

### If an Error Repeats
If the same class of error occurs twice:
- Escalate to structural review
- Refactor affected module
- Update docs to reflect new structure
- Continue execution

### If Architecture Is Flawed
You are allowed to:
- Reorganize apps
- Split large modules
- Rename confusing components

Provided:
- Domain invariants remain intact
- Changes are documented in docs/01_architecture.md
- Merge strategy remains valid

---

## BUILD PHASES (STRICT ORDER)

### PHASE 1 — Environment & Skeleton
- Initialize Django project
- Initialize React project
- Configure Docker Compose
- Verify Postgres connectivity
- Verify backend boots
- Verify frontend boots

**Do not proceed unless both servers start successfully.**

---

### PHASE 2 — Backend Core
Implement fully:
- JWT authentication
- Patients CRUD
- Modality & Service catalog
- Accession auto-generation
- Study lifecycle

Validate via API tests.

---

### PHASE 3 — Template Builder
Implement:
- Template CRUD
- Section CRUD
- Field CRUD
- Option CRUD
- Schema preview
- Version publishing
- Version immutability enforcement

If schema design proves limiting:
- Improve schema structure
- Update reporting engine accordingly
- Document rationale

---

### PHASE 4 — Reporting Engine
Implement:
- Draft report auto-creation
- Schema-driven value storage
- Draft saving
- Finalization lock
- PDF generation

PDF must be:
- Deterministic
- Stored
- Downloadable

---

### PHASE 5 — Frontend
Implement all screens:
- Login
- Dashboard
- Patients
- Catalog
- Templates
- Studies (worklist)
- Report Editor

Frontend MUST:
- Render forms dynamically from schema
- Respect finalized lock
- Surface errors clearly

---

### PHASE 6 — Data Seeding
Seed realistic demo data:
- ≥10 patients
- ≥8 services
- ≥10 studies
- ≥1 published template
- ≥1 finalized report with PDF

---

### PHASE 7 — VALIDATION (NO EXCEPTIONS)

You MUST prove:

Patient → Service → Study → Template → Draft → Final → PDF

If ANY step fails:
- Fix
- Re-test entire chain

---

## DOCUMENTATION OBLIGATIONS

You MUST update or add:
- docs/01_architecture.md (if structure changes)
- docs/02_domain_model.md (if schema evolves)
- docs/99_jules_master_prompt.md (append execution notes)

Add a final section:
## Jules Execution Log
- Summary of actions
- Deviations from original plan
- Reasons for deviations

---

## STOP CONDITION (ABSOLUTE)

STOP ONLY WHEN:
- System runs without errors
- All workflows pass
- PDF generation verified
- No manual DB edits required
- Application usable by non-technical user

---

## FINAL OUTPUT REQUIRED

Produce:
1. Phase-by-phase PASS/FAIL
2. URLs tested
3. Seeded credentials
4. Known limitations
5. Next steps (≤5)

DO NOT ask questions.
DO NOT wait.
EXECUTE UNTIL COMPLETE.
