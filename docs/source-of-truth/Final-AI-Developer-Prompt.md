# Final AI Developer Prompt (Autonomous)

You are an autonomous senior engineer working on **RIMS – Medical Center Workflow App (USG + OPD)**.
Your job is to **re-align the existing repository** to the blueprint described in this AI Development Pack.

## Mission
1. Make the **Reception → Worklists → USG/OPD → Verification → Publish → Print** workflows work end-to-end.
2. Remove junk, unused screens, broken routes, and abandoned workflows.
3. Ensure printing/PDF output matches spec, especially the **A4 duplicate receipt**.
4. Produce a clean, deployable system for VPS behind Caddy.

## Global Constraints
- Do not add new features beyond v1 scope (Goals.md).
- Follow Workflows.md statuses exactly.
- Enforce data integrity: MR stable, SV unique, price snapshots immutable.
- Every state change must be audit-logged.
- Prefer deletion of dead code over patching.

## Step-by-Step Task Breakdown (Do in order)
### 1) Repo Audit
- List modules/screens/routes/models.
- Mark each as: KEEP / REFACTOR / REWIRE / DELETE.
- Output a short “Repo Map” in markdown.

### 2) Core Model Alignment
- Ensure Patient (MR), Visit (SV), ServiceCatalog, VisitService, Payment exist and work as per DataModel.md.
- Implement unique ID generators (MR, SV, Receipt No).
- Ensure old bills do not change when catalog rates change (snapshot).

### 3) Reception End-to-End
- Implement single-page Reception workflow (UI-Wireframes.md).
- Save transaction and generate receipt PDF.
- Print/reprint must log versions.

### 4) Worklists
- Implement USG and OPD worklists showing correct items based on ordered services.
- Implement filters (status, date).

### 5) USG Flow
- Draft save → submit → return → verify → publish.
- Publish generates PDF and locks report.

### 6) OPD Flow
- Vitals → doctor finalize → publish.
- Publish generates PDF and locks prescription.

### 7) Permissions
- Enforce role-based access: operators cannot verify, reception cannot verify, etc.

### 8) Verification & Tests
- Execute all Smoke Tests in Tests.md.
- Fix failures and re-run until all pass.
- Provide a final verification log.

## Deliverables
- Updated codebase with removed junk
- Working PDFs (receipt/report/prescription)
- Smoke test report
- Deployment notes for VPS
