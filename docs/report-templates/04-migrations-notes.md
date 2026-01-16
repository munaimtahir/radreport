# Migration Notes

## Additive changes only
- New models are introduced in `apps/templates` for report templates and service linking.
- New `ReportTemplateReport` model is introduced in `apps/reporting` to store dynamic form values.
- No destructive migrations or model renames were performed.

## Legacy reporting
- Existing `Report` and `USGReport` models are unchanged.
- New template reporting persists values separately to avoid collisions with legacy data structures.
