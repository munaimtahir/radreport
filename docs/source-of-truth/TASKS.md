# TASKS.md (Repo Alignment Checklist)

## Phase A — Freeze & Audit
- [ ] Freeze feature work (no new features)
- [ ] Inventory existing routes/screens/models
- [ ] Identify duplicate or unused modules

## Phase B — Enforce Core Model
- [ ] Patient MR generation (unique, stable)
- [ ] Visit SV generation (unique)
- [ ] ServiceCatalog + price snapshots in VisitService
- [ ] Payment model with discount/paid/due

## Phase C — Worklists & State Machines
- [ ] USG statuses + transitions
- [ ] OPD statuses + transitions
- [ ] Audit log on each transition

## Phase D — Printing/PDF
- [ ] A4 duplicate receipt PDF (ReportLab)
- [ ] USG report PDF templates
- [ ] OPD prescription PDF templates
- [ ] Reprint center + version logs

## Phase E — Permissions
- [ ] Reception role
- [ ] USG operator role
- [ ] Verifier role
- [ ] OPD operator role
- [ ] Doctor role
- [ ] Admin role

## Phase F — Verification
- [ ] Execute all Smoke Tests (Tests.md)
- [ ] Fix failures
- [ ] Re-run smoke tests
