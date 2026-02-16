# Narrative Engine V2 — Documentation (Updated)

## What changed in this upgrade (Reporting Intelligence)

This upgrade focuses on **coherence** and **clinical readability** without changing your overall data model or breaking production output.

### Key improvements (safe + backwards compatible)

**Generator (`narrative_v2.py`)**
1. **Composite conditions** (new):
   - Supports `all` / `any` / `not` so templates can express real clinical logic without nesting multiple `if`s.
2. **Numeric-safe comparisons**:
   - `gt/gte/lt/lte` now coerce numeric strings safely (e.g., `"6"` behaves like `6`).
3. **Optional placeholders + defaults** (new):
   - Required: `{{field}}`
   - Optional: `{{field?}}`
   - Defaults: `{{field|N/A}}` and `{{field?|N/A}}`
   - This reduces “entire sentence disappears” behavior when an optional value is blank.

**Composer (`narrative_composer.py`)**
1. **No hard sentence truncation**:
   - Previously organ paragraphs were capped (e.g., 2 sentences). Now **all generated sentences are kept** in a single paragraph.
2. **Topic-driven ordering for natural flow**:
   - Within each organ, findings are arranged as: visibility → size → parenchyma → lesions → ducts/vessels → other → negatives.
3. **Visibility dominance**:
   - If an organ is “not visualized / obscured”, that becomes the organ paragraph and prevents contradictory extra statements.
4. **Cleaner grammar for Gallbladder/CBD**:
   - Avoids “is shows …” style errors when the clause starts with a verb like “shows”.
5. **Kidney section is more stable**:
   - Baseline measurement sentence is always produced first (if available), then side-specific abnormalities, then negatives.
6. **Better deduplication**:
   - Removes exact duplicates and also drops short lines that are already contained inside a longer sentence.

**Forward compatibility (important)**
- Composer now supports section lines as either:
  - legacy strings: `"Right kidney measures 10.5 cm."`
  - or dict atoms: `{"text": "...", "source_key": "kid_r_length_cm", "organ": "kidneys", "side": "R"}`  
  This allows templates (or the generator later) to pass richer metadata **without changing the API response shape**.

---

## Architecture & Data Flow

```
ReportTemplateV2.narrative_rules (JSON)
    ↓
generate_narrative_v2(template_v2, values_json)
    ↓
narrative_v2.py processes rules → generates sections + impression
    ↓
compose_narrative(narrative_json)
    ↓
narrative_json now includes:
  - sections (original)
  - impression (list)
  - narrative_by_organ (organ paragraphs)
  - narrative_text (full text)
    ↓
Stored in ReportInstanceV2.narrative_json
    ↓
PDF generator consumes narrative_json
```

---

## Narrative Rules Schema (Backward Compatible + Extended)

### Supported structure

```json
{
  "computed_fields": {
    "field_name": "expression"
  },
  "sections": [
    {
      "title": "Section Title",
      "content": [
        "Template string with {{field}} placeholders",
        {
          "if": { "field": "x", "gt": 5 },
          "then": "text",
          "else": "optional"
        }
      ]
    }
  ],
  "impression_rules": [
    {
      "priority": 1,
      "when": { "field": "x", "equals": true },
      "text": "Impression text",
      "continue": true
    }
  ]
}
```

### New: Composite conditions

```json
{
  "if": {
    "all": [
      { "field": "cbd_mm", "gt": 6 },
      { "field": "intrahepatic_dilated", "equals": true }
    ]
  },
  "then": "Biliary dilatation noted."
}
```

Also supported:
- `"any": [ ... ]`
- `"not": { ... }`

### New: Optional placeholders + defaults

- Required: `{{field}}`
- Optional: `{{field?}}` (if missing → becomes blank, sentence still renders)
- Default: `{{field|N/A}}`
- Optional with default: `{{field?|N/A}}`

Example:

```json
"content": [
  "The CBD measures {{cbd_mm}} mm ({{cbd_comment?|not specified}})."
]
```

If `cbd_comment` is blank, sentence remains valid.

---

## Output Structure (unchanged)

```json
{
  "sections": [...],
  "impression": [...],
  "computed": {...},
  "narrative_by_organ": [
    {"organ": "liver", "label": "Liver", "paragraph": "..." }
  ],
  "narrative_text": "Liver: ...\nKidneys: ..."
}
```

---

## Where to modify in future

### To enhance narrative intelligence further (next iterations)
1. **Add explicit organ/side metadata in templates** (recommended)
   - Start emitting dict lines: `{text, organ, side, source_key}`.
   - This removes the need for heuristic inference.
2. **Introduce “style profiles”**
   - e.g., “concise” vs “detailed” narrative output.
3. **Add domain-specific topic ordering per template**
   - Allow templates to override the organ topic order (e.g., vascular-first for Doppler).
4. **Add “conflict resolution” rules**
   - Example: if “not visualized”, drop measurement statements automatically (already partially handled).
5. **Add structured “negatives pack” per organ**
   - Template can define standard negative bundles (e.g., liver: {no focal lesion, no IHBD dilatation, no ascites}).

---

## Notes

- This upgrade is designed to be **safe in production**:
  - Output shape remains identical
  - Existing templates remain valid
  - New features (composite conditions, optional placeholders) are additive
