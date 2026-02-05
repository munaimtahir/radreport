# LIMS Catalog Import Packs (Sheet-A Core) — ALL Departments

## What these files are for
These XLSX files are prepared for the **two-stage** import flow you validated:

- **Stage-1:** creates base entities (Tests, Parameters, Panels)
- **Stage-2:** creates dependent links (Mapping, PanelTests, ReferenceRanges)

**Upload order is mandatory:** Stage-1 first, then Stage-2.

## Critical importer constraints (already respected)
- `test_id` / `parameter_id` / `panel_id` are **integers**
- `turnaround_time` is **numeric hours** (e.g., 24/48/72)
- Boolean fields use **TRUE/FALSE** (uppercase)
- `decimal_places` is provided for every parameter (qualitative fields use 0)
- Avoid placeholder tokens like "NA" in required fields

## Files included
### A) Combined (recommended)
- `LIMS_Catalog_STAGE1_ALL_Tests_Parameters_Panels.xlsx`
- `LIMS_Catalog_STAGE2_ALL_Mapping_PanelTests_ReferenceRanges.xlsx`

### B) Department-wise (optional, smaller batch uploads)
For each department, upload Stage-1 then Stage-2:
- `LIMS_Hematology_STAGE1.xlsx` + `LIMS_Hematology_STAGE2.xlsx`
- `LIMS_Biochemistry_STAGE1.xlsx` + `LIMS_Biochemistry_STAGE2.xlsx`
- `LIMS_Serology_Immunology_STAGE1.xlsx` + `LIMS_Serology_Immunology_STAGE2.xlsx`
- `LIMS_Microbiology_STAGE1.xlsx` + `LIMS_Microbiology_STAGE2.xlsx`
- `LIMS_Histopathology_STAGE1.xlsx` + `LIMS_Histopathology_STAGE2.xlsx`
- `LIMS_General_Lab_Clinical_Pathology_STAGE1.xlsx` + `LIMS_General_Lab_Clinical_Pathology_STAGE2.xlsx`

### C) Reference / Groundwork
- `LIMS_SheetA_CoreTests_Rebuilt_AllDepartments.xlsx` (your Sheet-A rebuilt master; human-readable + traceability)

### D) Source reference files (not for import)
- `LIMS_TestCatalog_*.xlsx` (uploaded source catalogs used only as reference)

## Suggested import workflow
1. Import **ALL Stage-1** file.
2. Verify created counts (Tests/Parameters/Panels).
3. Import **ALL Stage-2** file.
4. Verify Mapping/PanelTests/ReferenceRanges resolve.

If you prefer incremental rollout:
- Do Hematology Stage-1 + Stage-2, verify end-to-end.
- Then proceed department by department.
