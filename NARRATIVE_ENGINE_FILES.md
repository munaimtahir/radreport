# Narrative Engine V2 - File Reference

## Quick File Map

### Core Engine Files (Primary Focus for Updates)

| File | Purpose | Key Functions/Classes |
|------|---------|----------------------|
| `backend/apps/reporting/services/narrative_v2.py` | **Main narrative generator** - Executes rules, processes conditions, generates sections/impression | `generate_narrative_v2()`, `safe_eval()`, `_process_sections()`, `_process_impression()`, `_evaluate_condition()`, `_render_template()` |
| `backend/apps/reporting/services/narrative_composer.py` | **Narrative formatter** - Organizes narrative into organ-based paragraphs | `compose_narrative()`, `NarrativeAtom`, `compose_organ_paragraph()`, `_infer_organ()`, `_infer_kind()`, `_compose_kidneys()`, `_compose_gallbladder_cbd()` |

### Model & Data Structure

| File | Purpose | Key Components |
|------|---------|----------------|
| `backend/apps/reporting/models.py` | Database model - Stores narrative_rules | `ReportTemplateV2.narrative_rules` (JSONField), `ReportInstanceV2.narrative_json` |
| `backend/apps/reporting/serializers.py` | API serialization - Validates narrative_rules | `ReportTemplateV2Serializer`, `validate_narrative_rules()` |

### API Integration

| File | Purpose | Key Endpoints |
|------|---------|---------------|
| `backend/apps/reporting/views.py` | API views - Exposes narrative generation endpoints | `generate_narrative()`, `narrative()`, `preview_narrative()`, `publish()` |

### PDF Generation

| File | Purpose | Key Functions |
|------|---------|---------------|
| `backend/apps/reporting/pdf_engine/report_pdf_v2.py` | PDF generator - Consumes narrative_json for PDF output | `generate_report_pdf_v2()`, `ReportPDFGeneratorV2` |

### Template Files (Rule Definitions)

| Location | Purpose |
|----------|---------|
| `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/*.json` | Template JSON files containing `narrative_rules` definitions |

### Test Files

| File | Purpose | Test Coverage |
|------|---------|---------------|
| `backend/apps/reporting/tests/test_narrative_logic_v2.py` | Tests rule processing logic | Computed fields, conditionals, operators, impressions |
| `backend/apps/reporting/tests/test_narrative_composer.py` | Tests composition logic | Organ grouping, paragraph formatting, deduplication |
| `backend/apps/reporting/tests/test_workitem_v2_narrative.py` | Integration tests | API endpoints, end-to-end flow |

### Debug & Utilities

| File | Purpose |
|------|---------|
| `backend/debug_narrative.py` | Manual testing script for narrative generation |

---

## Update Workflow

### Scenario 1: Add New Operator/Condition

**Files to modify:**
1. `backend/apps/reporting/services/narrative_v2.py`
   - Add operator in `_evaluate_condition()`
   - Update tests in `test_narrative_logic_v2.py`

### Scenario 2: Add New Organ Handler

**Files to modify:**
1. `backend/apps/reporting/services/narrative_composer.py`
   - Add `_compose_organname()` function
   - Update `compose_organ_paragraph()` to call it
   - Add organ to `ORGAN_ORDER` and `ORGAN_LABELS`
   - Update tests in `test_narrative_composer.py`

### Scenario 3: Change Output Structure

**Files to modify:**
1. `backend/apps/reporting/services/narrative_composer.py` - Output format
2. `backend/apps/reporting/pdf_engine/report_pdf_v2.py` - PDF consumption
3. `backend/apps/reporting/views.py` - API response format
4. All test files - Update assertions

### Scenario 4: Add New Math Function

**Files to modify:**
1. `backend/apps/reporting/services/narrative_v2.py`
   - Add function to `SafeEvaluator.functions` dict
   - Update tests

### Scenario 5: Change Template Schema

**Files to modify:**
1. `backend/apps/reporting/models.py` - Field definition (if needed)
2. `backend/apps/reporting/serializers.py` - Validation logic
3. `backend/apps/reporting/services/narrative_v2.py` - Processing logic
4. Template JSON files - Update structure
5. All test files

---

## Code Statistics

- **narrative_v2.py**: ~265 lines
- **narrative_composer.py**: ~478 lines
- **Total core engine**: ~743 lines
- **Test coverage**: 3 test files with ~15+ test cases

---

## Entry Points

1. **API**: `POST /api/reporting/workitems/{id}/generate-narrative/`
2. **Direct**: `generate_narrative_v2(template_v2, values_json)`
3. **Debug**: `python backend/debug_narrative.py`
