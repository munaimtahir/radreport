# Narrative Engine V2 - Complete Documentation

## Overview

The Narrative Engine V2 is a rule-based system that generates medical report narratives from structured form data (`values_json`) using template-defined rules (`narrative_rules`). It consists of two main components:

1. **Narrative Generator** (`narrative_v2.py`) - Executes rules and generates structured narrative JSON
2. **Narrative Composer** (`narrative_composer.py`) - Formats and organizes narrative into organ-based paragraphs

---

## Architecture & File Structure

### Core Engine Files

```
backend/apps/reporting/services/
├── narrative_v2.py              # Main narrative generation engine
└── narrative_composer.py         # Narrative formatting and composition

backend/apps/reporting/
├── models.py                     # ReportTemplateV2 model (contains narrative_rules JSONField)
├── views.py                      # API endpoints that use narrative engine
└── pdf_engine/report_pdf_v2.py  # PDF generator (consumes narrative_json)

backend/apps/reporting/tests/
├── test_narrative_logic_v2.py    # Tests for narrative_v2 logic
├── test_narrative_composer.py    # Tests for composer logic
└── test_workitem_v2_narrative.py # Integration tests

backend/debug_narrative.py        # Debug script for testing narrative generation
```

### Data Flow

```
ReportTemplateV2.narrative_rules (JSON)
    ↓
generate_narrative_v2(template_v2, values_json)
    ↓
narrative_v2.py processes rules → generates sections/impression
    ↓
compose_narrative(narrative_json) → formats into organ-based paragraphs
    ↓
narrative_json (with sections, narrative_by_organ, narrative_text)
    ↓
Stored in ReportInstanceV2.narrative_json
    ↓
Used by PDF generator and API responses
```

---

## Core Components

### 1. Narrative Generator (`narrative_v2.py`)

**Main Function:**
```python
generate_narrative_v2(template_v2, values_json: dict, include_composer_debug: bool = False) -> dict
```

**Process Flow:**
1. **Computed Fields** - Evaluates mathematical expressions
2. **Sections Processing** - Conditional narrative generation
3. **Impression Synthesis** - Priority-based impression rules
4. **Composition** - Passes to composer for formatting

**Key Functions:**

- `safe_eval(expr, context)` - Safe expression evaluator for computed fields
  - Uses AST parsing for security
  - Supports: `+`, `-`, `*`, `/`, `**`, `abs()`, `round()`, `min()`, `max()`
  - Missing fields default to `0` for math operations

- `_process_sections(sections_def, values, schema)` - Processes section rules
  - Returns list of `{title, lines}` dictionaries
  - Preserves deterministic ordering

- `_process_rule(rule, values, schema)` - Processes individual rules
  - Handles strings, lists, and conditional dicts (`if/then/else`)
  - Recursive processing for nested rules

- `_process_impression(rules, values, schema)` - Impression synthesis
  - Sorts by priority (ascending)
  - Multiple matches allowed unless `continue: false`
  - Returns list of impression strings

- `_evaluate_condition(condition, values)` - Condition evaluation
  - Operators: `equals`, `not_equals`, `gt`, `gte`, `lt`, `lte`
  - Checks: `is_empty`, `is_not_empty`, `in`, `not_in`

- `_render_template(template, values, json_schema)` - Template rendering
  - Replaces `{{field}}` placeholders
  - Returns empty string if any placeholder is missing/empty

### 2. Narrative Composer (`narrative_composer.py`)

**Main Function:**
```python
compose_narrative(narrative_json: dict, values_json: Optional[dict] = None, include_debug: bool = False) -> dict
```

**Process Flow:**
1. **Atom Extraction** - Converts sections to `NarrativeAtom` objects
2. **Organ Grouping** - Groups atoms by organ (liver, kidneys, etc.)
3. **Paragraph Composition** - Generates organ-specific paragraphs
4. **Text Assembly** - Creates `narrative_by_organ` and `narrative_text`

**Key Concepts:**

- **NarrativeAtom** - Data class representing a narrative fragment
  ```python
  @dataclass
  class NarrativeAtom:
      organ: str          # "liver", "kidneys", "gallbladder_cbd", etc.
      side: str           # "R", "L", "B", "N" (Right, Left, Bilateral, None)
      kind: str           # "measurement", "status", "positive", "negative"
      priority: int       # Ordering priority
      text: str           # The narrative text
      source_key: str     # Optional source field key
  ```

- **Organ Inference** - Automatically detects organ from:
  - Field name prefixes (`liv_`, `kid_r_`, `gb_`, etc.)
  - Section titles ("Liver", "Kidney", etc.)
  - Text content keywords

- **Kind Inference** - Categorizes text as:
  - `negative` - Starts with "no" (case-insensitive)
  - `measurement` - Contains measurement keywords or numbers with units
  - `status` - Contains status keywords (normal, unremarkable, etc.)
  - `positive` - Default for abnormalities

- **Special Organ Handlers:**
  - `_compose_kidneys()` - Handles bilateral measurements, side-specific findings
  - `_compose_gallbladder_cbd()` - Merges gallbladder and CBD findings

**Output Structure:**
```python
{
    "sections": [...],                    # Original sections from generator
    "impression": [...],                  # Impression list
    "narrative_by_organ": [               # Formatted organ paragraphs
        {
            "organ": "liver",
            "label": "Liver",
            "paragraph": "The liver measures 14.5 cm..."
        },
        ...
    ],
    "narrative_text": "Liver: ...\nKidneys: ...",  # Full text
    "composer_debug": {...}               # Debug info (if requested)
}
```

---

## Narrative Rules Structure

Narrative rules are stored in `ReportTemplateV2.narrative_rules` (JSONField).

### Schema

```json
{
  "computed_fields": {
    "field_name": "expression"  // e.g., "abs(rk_size - lk_size)"
  },
  "sections": [
    {
      "title": "Section Title",
      "content": [
        "Simple string template with {{field}}",
        {
          "if": {
            "field": "field_name",
            "operator": "value"
          },
          "then": "text or nested rules",
          "else": "optional else clause"
        },
        ["array", "of", "rules"]  // All evaluated, results combined
      ]
    }
  ],
  "impression_rules": [
    {
      "priority": 1,              // Lower = higher priority
      "when": {
        "field": "field_name",
        "operator": "value"
      },
      "text": "Impression text with {{field}}",
      "continue": true             // Allow multiple matches
    }
  ]
}
```

### Example Template

```json
{
  "narrative_rules": {
    "computed_fields": {
      "renal_symmetry": "abs(kid_r_length_cm - kid_l_length_cm)"
    },
    "sections": [
      {
        "title": "Right kidney",
        "content": [
          {
            "if": {
              "field": "kid_r_visualized",
              "equals": true
            },
            "then": [
              {
                "if": {
                  "field": "kid_r_length_cm",
                  "is_not_empty": true
                },
                "then": "Right kidney measures {{kid_r_length_cm}} cm."
              },
              {
                "if": {
                  "field": "kid_r_cmd",
                  "is_not_empty": true
                },
                "then": "Corticomedullary differentiation is {{kid_r_cmd}}."
              }
            ]
          },
          {
            "if": {
              "field": "kid_r_calculus_present",
              "equals": true
            },
            "then": "Right renal calculus noted (largest {{kid_r_largest_calculus_mm}} mm)."
          }
        ]
      }
    ],
    "impression_rules": [
      {
        "priority": 1,
        "when": {
          "field": "kid_r_calculus_present",
          "equals": true
        },
        "text": "Right renal calculus.",
        "continue": true
      },
      {
        "priority": 2,
        "when": {
          "field": "kid_r_length_cm",
          "gt": 12
        },
        "text": "Right renal enlargement."
      }
    ]
  }
}
```

---

## API Integration

### Endpoints Using Narrative Engine

**Location:** `backend/apps/reporting/views.py`

1. **Generate Narrative** - `POST /api/reporting/workitems/{id}/generate-narrative/`
   - Generates narrative from current `values_json`
   - Saves to `instance.narrative_json`
   - Returns formatted narrative

2. **Get Narrative** - `GET /api/reporting/workitems/{id}/narrative/`
   - Returns stored narrative or generates on-the-fly (if debug mode)
   - Includes `narrative_by_organ` and `narrative_text`

3. **Preview Narrative** - `POST /api/reporting/templates-v2/{id}/preview-narrative/`
   - Preview narrative for given `values_json`
   - Does not save to instance

4. **Report PDF** - `GET /api/reporting/workitems/{id}/report-pdf/`
   - Generates PDF using narrative_json
   - Calls `generate_report_pdf_v2()` which consumes narrative_json

5. **Publish** - `POST /api/reporting/workitems/{id}/publish/`
   - Generates narrative if not present
   - Creates `ReportPublishSnapshotV2` with narrative_json

---

## Key Design Decisions

### 1. Deterministic Ordering
- Sections processed in definition order
- Impression rules sorted by priority (stable sort preserves author order)
- Atoms sorted by priority within organs

### 2. Missing Field Handling
- Template rendering returns empty string if any `{{field}}` is missing
- Computed fields default missing values to `0` for math safety
- Conditional rules evaluate to `None` if condition fails

### 3. Organ-Based Composition
- Automatically groups findings by anatomical organ
- Special handling for kidneys (bilateral) and gallbladder/CBD
- Negative findings compressed and deduplicated

### 4. Safe Expression Evaluation
- Uses AST parsing (not `eval()`) for security
- Limited operator set (no function calls except whitelist)
- Missing fields handled gracefully

### 5. Multi-Hit Impression Rules
- By default, multiple impression rules can match
- Use `continue: false` to stop after first match
- Priority determines evaluation order

---

## Files to Modify for Updates

### To Update Narrative Generation Logic:

1. **`backend/apps/reporting/services/narrative_v2.py`**
   - Modify `_process_sections()` for section processing changes
   - Modify `_process_impression()` for impression logic changes
   - Modify `_evaluate_condition()` for new operators
   - Modify `safe_eval()` for new math functions

2. **`backend/apps/reporting/services/narrative_composer.py`**
   - Modify `compose_narrative()` for output structure changes
   - Modify `compose_organ_paragraph()` for paragraph formatting
   - Modify `_infer_organ()` for new organ detection
   - Modify `_infer_kind()` for new text categorization
   - Add new organ handlers (e.g., `_compose_pancreas()`)

### To Update Template Structure:

1. **`backend/apps/reporting/models.py`**
   - Modify `ReportTemplateV2.narrative_rules` field if schema changes
   - Update validation in serializer if needed

2. **`backend/apps/reporting/serializers.py`**
   - Update `validate_narrative_rules()` for schema validation

3. **Template JSON files** (`backend/apps/reporting/seed_data/templates_v2/`)
   - Update narrative_rules structure in template files

### To Update API Behavior:

1. **`backend/apps/reporting/views.py`**
   - Modify `generate_narrative()` action
   - Modify `narrative()` action
   - Modify `preview_narrative()` action

### To Update PDF Output:

1. **`backend/apps/reporting/pdf_engine/report_pdf_v2.py`**
   - Modify how narrative_json is consumed
   - Update PDF layout if narrative structure changes

---

## Testing

### Test Files

1. **`test_narrative_logic_v2.py`** - Tests rule processing
   - Computed fields
   - Conditional logic
   - Operators
   - Impression synthesis

2. **`test_narrative_composer.py`** - Tests composition
   - Organ grouping
   - Paragraph formatting
   - Deduplication
   - Order stability

3. **`test_workitem_v2_narrative.py`** - Integration tests
   - API endpoints
   - End-to-end flow

### Debug Script

**`backend/debug_narrative.py`** - Manual testing script
```bash
cd backend
python debug_narrative.py
```

---

## Current Limitations & Known Issues

1. **Template Rendering** - Returns empty string if ANY placeholder missing
   - May skip entire sections if one field is empty
   - Consider partial rendering option

2. **Organ Inference** - Heuristic-based, may misclassify
   - Relies on field prefixes and text keywords
   - Could benefit from explicit organ tagging in rules

3. **Negative Compression** - Limited to 3 items
   - Hard-coded limit in `_compress_negatives()`

4. **Sentence Limit** - Paragraphs limited to 2 sentences
   - Hard-coded in `_cap_sentences()`

5. **No Custom Functions** - Limited math functions
   - Only: `abs`, `round`, `min`, `max`
   - No string manipulation functions

6. **No Loops/Iteration** - Cannot iterate over arrays
   - Cannot generate "Multiple stones: 5mm, 8mm, 12mm"

---

## Recommended Update Areas

### High Priority

1. **Partial Template Rendering** - Allow sections with some missing fields
2. **Explicit Organ Tagging** - Add `organ` field to rules for better control
3. **Array Iteration** - Support loops for multiple findings
4. **String Functions** - Add `join()`, `upper()`, `lower()`, `capitalize()`

### Medium Priority

1. **Custom Organ Handlers** - Make organ composition configurable
2. **Narrative Templates** - Support template inheritance/composition
3. **Validation** - Schema validation for narrative_rules
4. **Performance** - Caching for computed fields

### Low Priority

1. **Internationalization** - Multi-language narrative generation
2. **Style Variants** - Different narrative styles per template
3. **AI Integration** - Optional LLM-based narrative enhancement

---

## Example Usage

### Generating Narrative

```python
from apps.reporting.models import ReportTemplateV2
from apps.reporting.services.narrative_v2 import generate_narrative_v2

template = ReportTemplateV2.objects.get(code="USG_KUB_V1")
values = {
    "kid_r_visualized": True,
    "kid_r_length_cm": 10.5,
    "kid_r_cmd": "preserved",
    "kid_r_calculus_present": True,
    "kid_r_largest_calculus_mm": 5
}

narrative = generate_narrative_v2(template, values)
print(narrative["narrative_text"])
# Output: "Right kidney: The right kidney measures 10.5 cm with preserved 
#          corticomedullary differentiation. Right renal calculus noted 
#          (largest 5 mm)."
```

### API Call

```bash
# Generate narrative
curl -X POST http://localhost:8000/api/reporting/workitems/{id}/generate-narrative/ \
  -H "Authorization: Bearer {token}"

# Get narrative
curl http://localhost:8000/api/reporting/workitems/{id}/narrative/ \
  -H "Authorization: Bearer {token}"
```

---

## Summary

The Narrative Engine V2 is a **rule-based, deterministic system** that:
- Generates structured narratives from form data
- Supports computed fields, conditional logic, and impression synthesis
- Formats output into organ-based paragraphs
- Integrates with PDF generation and API endpoints

**To update the engine, focus on:**
- `narrative_v2.py` for generation logic
- `narrative_composer.py` for formatting logic
- Template JSON files for rule definitions
- Test files to verify changes
