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
    - [ ] Set **Free Fluid Present** to `Yes`.
        - [ ] Verify `Free Fluid Amount` is VISIBLE.
- [ ] **Data Integrity**:
    - [ ] Fill out the form.
    - [ ] Click "Save Draft".
    - [ ] Reload page.
    - [ ] specific values should persist.
    - [ ] Check "Narrative JSON" box at bottom (if available) or Chrome Network tab to ensure `values_json` has standard keys (e.g. `liv_size_cm`, not nested in some UI group).

### 3. Edge Cases
- [ ] Toggle "Liver Visualized" `No` -> Save -> Reload. Fields should remain hidden but if data was present before hiding, ensure backend didn't lose it (UI hides it, but data might persist in JSON depending on implementation. *Note: Current implementation hides UI but doesn't delete data automatically unless manual clear logic added. This maintains safety.*)

## Troubleshooting
- If UI is blank, check Console for `SmartSchemaFormV2` errors.
- If specific fields are missing unexpectedly, check `USG_ABD_V1.ts` visibility rules.
