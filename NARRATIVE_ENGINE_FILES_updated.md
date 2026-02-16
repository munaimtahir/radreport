# Narrative Engine V2 — File Reference (Updated)

This update adds **safe intelligence improvements** without changing the API response shape.

---

## Core Engine Files (Primary)

| File | Purpose | Notes (after upgrade) |
|------|---------|------------------------|
| `backend/apps/reporting/services/narrative_v2.py` | Rule execution engine | Adds composite conditions + optional placeholders/defaults |
| `backend/apps/reporting/services/narrative_composer.py` | Narrative composer/formatter | Removes hard sentence cap, adds topic ordering, better dedupe, fixes GB/CBD grammar |

---

## Important Behavior Changes

### 1) Template placeholders (generator)
- Required: `{{field}}` → sentence skipped if missing
- Optional: `{{field?}}` → missing becomes blank, sentence can still render
- Default: `{{field|N/A}}` or `{{field?|N/A}}`

### 2) Condition operators (generator)
- Existing: `equals`, `not_equals`, `gt`, `gte`, `lt`, `lte`, `is_empty`, `is_not_empty`, `in`, `not_in`
- New: composite conditions:
  - `{ "all": [ ... ] }`
  - `{ "any": [ ... ] }`
  - `{ "not": { ... } }`
- Numeric comparisons now safely handle numeric strings.

### 3) Composition (composer)
- One paragraph per organ is preserved, but:
  - **No hard truncation** of sentences
  - **Topic-driven ordering** inside each organ
  - **Visibility dominance** (not visualized overrides)
  - **Kidneys** always start with baseline measurement if present
  - **Gallbladder/CBD** clause grammar fixed

---

## Forward-Compatible Line Format (Composer)

Legacy (still supported):
```json
{"title":"Liver","lines":["The liver measures 14 cm.","No focal lesion."]}
```

New (supported for future smarter templates):
```json
{"title":"Right kidney","lines":[
  {"text":"Right kidney measures 10.5 cm.","organ":"kidneys","side":"R","source_key":"kid_r_length_cm"},
  {"text":"Corticomedullary differentiation is preserved.","organ":"kidneys","kind":"status"}
]}
```

---

## Update Workflow

### Add a new organ handler
1. `narrative_composer.py`
   - Add a new `_compose_<organ>()` function.
   - Register it in `compose_organ_paragraph()`.
   - Add label in `ORGAN_LABELS` and ordering in `ORGAN_ORDER`.
2. Add tests in `test_narrative_composer.py`.

### Add new condition / operator
1. `narrative_v2.py`
   - Add logic in `_evaluate_condition()`.
2. Add tests in `test_narrative_logic_v2.py`.

### Adjust rendering behavior
1. `narrative_v2.py`
   - Update `_render_template()` placeholder logic.
2. Add tests for optional/default placeholders.

---

## Code Stats (approx.)
- Generator: ~300–350 lines (after upgrade)
- Composer: ~500–650 lines (after upgrade; mostly new helpers)

---

## Entry Points (unchanged)
1. API: `POST /api/reporting/workitems/{id}/generate-narrative/`
2. Direct: `generate_narrative_v2(template_v2, values_json)`
3. Preview: `POST /api/reporting/templates-v2/{id}/preview-narrative/`
