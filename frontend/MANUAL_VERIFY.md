# Manual Verification for Enhanced Reporting UI

## Prerequisites
1. Ensure backend is running (`./develop.sh` or `docker compose up`).
2. Login to frontend (`localhost:5173`).
3. Navigate to a Reporting task for "USG Abdomen" (Create an order for USG Abdomen if needed).

## Checklist

### 1. Fallback Behavior (Regression Test)
- [ ] Open a report for a template **OTHER THAN** USG Abdomen (e.g. USG KUB or USG Pelvis).
- [ ] Verify the UI renders exactly as before (standard stacked fields).
- [ ] Ensure no errors in console.
- [ ] Verify data entry and saving still works.

### 2. USG Abdomen Enhanced UI
- [ ] Open a USG Abdomen report.
- [ ] **Appearance**: Verify layout is cleaner.
    - [ ] Units (cm, mm) are shown inside input fields on the right.
    - [ ] Labels like "Corticomedullary differentiation" are used instead of `kid_r_cmd`.
- [ ] **Paired Groups**:
    - [ ] Locate "Kidneys" section.
    - [ ] Verify "Right" and "Left" columns are displayed side-by-side.
    - [ ] Verify fields like length, echogenicity match the correct side.
- [ ] **Visibility Rules**:
    - [ ] Set **Liver Visualized** to `No`.
        - [ ] Verify `Liver Size`, `Contour`, `Echogenicity` fields DISAPPEAR immediately.
        - [ ] Verify `Limitation Reason` REMAINS visible.
    - [ ] Set **Liver Visualized** back to `Satisfactory`.
        - [ ] Verify fields REAPPEAR.
    - [ ] Set **Free Fluid Present** to `No` (or uncheck if checkbox).
        - [ ] Verify `Free Fluid Amount` is HIDDEN.
    - [ ] Set **Aorta/IVC Visualized** to `Obscured`.
        - [ ] Verify `Aorta Max Diameter (mm)` is HIDDEN.
    - [ ] Set **R Kidney Calculus Present** to `No`.
        - [ ] Verify `R Kidney Largest Calculus (mm)` is HIDDEN.
- [ ] **Data Integrity**:
    - [ ] Fill out the form.
    - [ ] Click "Save Draft".
    - [ ] Reload page.
    - [ ] specific values should persist.
    - [ ] Check "Narrative JSON" box at bottom (if available) or Chrome Network tab to ensure `values_json` has standard keys (e.g. `liv_size_cm`, not nested in some UI group).

### 3. USG KUB Enhanced UI
- [ ] Open a USG KUB report (Template Code: `USG_KUB_V1`).
- [ ] **Paired Groups**:
    - [ ] Verify **Kidneys** are in side-by-side columns.
    - [ ] Verify **Ureters** are in side-by-side columns.
- [ ] **Visibility Rules**:
    - [ ] Set **Right Kidney Visualized** to `No`.
        - [ ] Verify all right kidney detail fields disappear.
    - [ ] Set **Right Kidney Calculus Present** to `No`.
        - [ ] Verify `Right Kidney Largest Calculus (mm)` disappears.
    - [ ] Set **Right Ureter Stone Suspected** to `No`.
        - [ ] Verify `Stone Location (R)` and `Stone Size (mm) (R)` disappear.
    - [ ] Set **Bladder Visualized** to `No`.
        - [ ] Verify all bladder detail fields disappear.
- [ ] **Units**:
    - [ ] Verify `(cm)`, `(mm)`, and `(mL)` units are correctly displayed in measurements.
- [ ] **Data Integrity**:
    - [ ] Verify values persist after save/reload.
    - [ ] Verify hidden fields are not tabbable/focusable.

### 4. USG Pelvis Enhanced UI
- [ ] Open a USG Pelvis report (Template Code: `USG_PELVIS_V1`).
- [ ] **Paired Groups**:
    - [ ] Verify **Ovaries** are in side-by-side columns.
- [ ] **Visibility Rules**:
    - [ ] Set **Fibroid Present** to `No`.
        - [ ] Verify `Largest Fibroid (mm)` disappears.
    - [ ] Set **Adnexal Mass Present** to `No`.
        - [ ] Verify `Adnexa Side`, `Papillary Projection`, `Solid Component`, etc. disappear.
- [ ] **Data Integrity**:
    - [ ] Verify values persist after save/reload.

### 5. Developer Tools (Spec Lint)
- [ ] Open Browser Console (F12) while on any Enhanced UI report.
- [ ] Verify no `[SpecLint]` warnings appear (unless deliberate errors exist).
- [ ] If warnings appear, verify they are actionable (e.g. "references unknown key").

### 6. Edge Cases

## Troubleshooting
- If UI is blank, check Console for `SmartSchemaFormV2` errors.
- If specific fields are missing unexpectedly, check `USG_ABD_V1.ts` visibility rules.
