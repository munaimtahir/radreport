"""
V2 Narrative Engine for JSON schema-based templates.

Executes narrative_rules from ReportTemplateV2 to generate narrative_json.

Core goals:
- Deterministic output
- Safe evaluation for computed fields (no eval)
- Backward compatible rule schema
- Forward compatible rendering & condition features

Supports:
- Computed fields (safe math expressions)
- Conditional logic (if/then/else)
- Impression rule synthesis
- Optional placeholders and defaults in templates (new)
- Composite conditions (all/any/not) (new)
"""

import logging
import re
import ast
import operator
from typing import Any, Dict, Optional, Sequence

from .narrative_composer import compose_narrative

logger = logging.getLogger(__name__)

# --- Safe Expression Evaluator for Computed Fields ---


class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, names: Dict[str, Any]):
        self.names = names
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
        }
        self.functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
        }

    def visit_BinOp(self, node):
        return self.operators[type(node.op)](self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node):
        return self.operators[type(node.op)](self.visit(node.operand))

    def visit_Compare(self, node):
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if not self.operators[type(op)](left, right):
                return False
            left = right
        return True

    def visit_Call(self, node):
        func_name = getattr(node.func, "id", None)
        if not func_name or func_name not in self.functions:
            raise ValueError(f"Function {func_name} not allowed")
        args = [self.visit(arg) for arg in node.args]
        return self.functions[func_name](*args)

    def visit_Name(self, node):
        val = self.names.get(node.id)
        if val is None:
            # For computed fields we prefer safe behavior over crashes.
            return 0
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    def visit_Constant(self, node):
        return node.value

    def generic_visit(self, node):
        raise ValueError(f"Operation not allowed: {type(node).__name__}")


def safe_eval(expr: str, context: Dict[str, Any]):
    try:
        if not expr:
            return None
        node = ast.parse(expr, mode="eval")
        evaluator = SafeEvaluator(context)
        return evaluator.visit(node.body)
    except Exception as e:
        logger.warning(f"Failed to evaluate expression '{expr}': {e}")
        return None


# --- Main Engine ---


def generate_narrative_v2(template_v2, values_json: dict, include_composer_debug: bool = False) -> dict:
    narrative_rules = template_v2.narrative_rules or {}

    # 1. Computed Fields
    computed_defs = narrative_rules.get("computed_fields", {}) or {}
    context_values = dict(values_json or {})

    for field_name, expr in computed_defs.items():
        val = safe_eval(expr, context_values)
        if val is not None:
            context_values[field_name] = val

    result: Dict[str, Any] = {}

    # 2. Process Sections (Conditional Narrative) with deterministic ordering
    sections_def = narrative_rules.get("sections", []) or []
    result["sections"] = _process_sections(sections_def, context_values, template_v2.json_schema)

    # 3. Impression Synthesis (multiple matches allowed)
    impression_rules = narrative_rules.get("impression_rules", []) or []
    result["impression"] = _process_impression(impression_rules, context_values, template_v2.json_schema)

    # Store computed values for reference
    computed_values = {k: context_values[k] for k in computed_defs.keys() if k in context_values}
    if computed_values:
        result["computed"] = computed_values

    return compose_narrative(result, values_json=values_json, include_debug=include_composer_debug)


def _process_sections(sections_def, values, schema):
    rendered_sections = []

    for section in sections_def:
        if not isinstance(section, dict):
            continue
        title = section.get("title", "")
        content_rules = section.get("content", [])

        rendered_lines = []
        for rule in content_rules:
            text = _process_rule(rule, values, schema)
            if text:
                if isinstance(text, list):
                    rendered_lines.extend(text)
                else:
                    rendered_lines.append(text)

        if rendered_lines:
            rendered_sections.append({"title": title, "lines": rendered_lines})

    # Preserve input ordering; no further sort here to keep deterministic output aligned to definition order.
    return rendered_sections


def _process_rule(rule, values, schema):
    """Process a single rule (string, list, or dict condition)."""
    if isinstance(rule, str):
        return _render_template(rule, values, schema)

    if isinstance(rule, list):
        results = []
        for r in rule:
            res = _process_rule(r, values, schema)
            if res:
                if isinstance(res, list):
                    results.extend(res)
                else:
                    results.append(res)
        return results if results else None

    if isinstance(rule, dict):
        # Conditional
        if "if" in rule:
            cond = rule.get("if")
            if _evaluate_condition(cond, values):
                if "then" in rule:
                    return _process_rule(rule.get("then"), values, schema)
            else:
                if "else" in rule:
                    return _process_rule(rule.get("else"), values, schema)

        # Or recursive list via "rules" key
        if "rules" in rule:
            return _process_rule(rule.get("rules"), values, schema)

    return None


def _process_impression(rules, values, schema):
    impressions = []

    # Sort deterministically by priority (ascending). Stable sort preserves author order for ties.
    sorted_rules = sorted(enumerate(rules), key=lambda x: (x[1].get("priority", 999), x[0]))

    for _, rule in sorted_rules:
        when = rule.get("when")
        if _evaluate_condition(when, values):
            text = rule.get("text", "")
            if text:
                rendered = _render_template(text, values, schema)
                if rendered:
                    impressions.append(rendered)

            # allow multiple matches; only stop when explicitly requested
            if not rule.get("continue", False):
                break

    return impressions


def _is_empty(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    if isinstance(val, (list, tuple, set, dict)) and len(val) == 0:
        return True
    return False


def _coerce_number(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    if isinstance(val, str):
        s = val.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _evaluate_condition(condition, values):
    """Evaluate condition dict.

    Backward compatible with existing schema.
    New (optional) composite operators:
      - {"all": [cond1, cond2, ...]}
      - {"any": [cond1, cond2, ...]}
      - {"not": cond}
    """
    if not condition:
        return True

    if isinstance(condition, dict):
        if "all" in condition and isinstance(condition["all"], list):
            return all(_evaluate_condition(c, values) for c in condition["all"])
        if "any" in condition and isinstance(condition["any"], list):
            return any(_evaluate_condition(c, values) for c in condition["any"])
        if "not" in condition:
            return not _evaluate_condition(condition["not"], values)

    field = condition.get("field") if isinstance(condition, dict) else None
    val = values.get(field) if field else None

    # Operators
    if "equals" in condition:
        return val == condition["equals"]
    if "not_equals" in condition:
        return val != condition["not_equals"]

    if "gt" in condition:
        left = _coerce_number(val)
        right = _coerce_number(condition["gt"])
        return left is not None and right is not None and left > right
    if "gte" in condition:
        left = _coerce_number(val)
        right = _coerce_number(condition["gte"])
        return left is not None and right is not None and left >= right
    if "lt" in condition:
        left = _coerce_number(val)
        right = _coerce_number(condition["lt"])
        return left is not None and right is not None and left < right
    if "lte" in condition:
        left = _coerce_number(val)
        right = _coerce_number(condition["lte"])
        return left is not None and right is not None and left <= right

    if "is_empty" in condition:
        return _is_empty(val)
    if "is_not_empty" in condition:
        return not _is_empty(val)

    if "in" in condition:
        pool = condition["in"]
        if isinstance(val, list):
            return any(v in pool for v in val)
        return val in pool

    if "not_in" in condition:
        pool = condition["not_in"]
        if isinstance(val, list):
            return all(v not in pool for v in val)
        return val not in pool

    # New lightweight string operator
    if "contains" in condition:
        needle = str(condition["contains"]).lower()
        return isinstance(val, str) and needle in val.lower()

    return False


# Template placeholders:
#   - required: {{field}}
#   - optional: {{field?}}
#   - default:  {{field|N/A}} or {{field?|N/A}}
_PLACEHOLDER_RX = re.compile(r"\{\{([^}]+)\}\}")


def _parse_placeholder(token: str) -> Dict[str, Any]:
    token = (token or "").strip()
    default = None
    if "|" in token:
        token, default = token.split("|", 1)
        token = token.strip()
        default = default.strip()

    optional = False
    if token.startswith("?"):
        optional = True
        token = token[1:].strip()
    if token.endswith("?"):
        optional = True
        token = token[:-1].strip()

    return {"field": token, "optional": optional, "default": default}


def _render_template(template: str, values: dict, json_schema: dict) -> str:
    # Find all {{...}} placeholders (supports optional/default).
    tokens = _PLACEHOLDER_RX.findall(template or "")
    if not tokens:
        return (template or "").strip()

    placeholders = [_parse_placeholder(t) for t in tokens]

    # Skip if any required placeholder is missing AND no default is provided.
    for ph in placeholders:
        if ph["optional"]:
            continue
        field = ph["field"]
        if not field:
            continue
        val = values.get(field)
        if _is_empty(val) and not ph["default"]:
            return ""

    def replace_field(match):
        ph = _parse_placeholder(match.group(1))
        field_name = ph["field"]
        val = values.get(field_name)
        if _is_empty(val):
            return ph["default"] or ""
        return _format_value(val, field_name, json_schema)

    rendered = _PLACEHOLDER_RX.sub(replace_field, template or "")
    # Normalize whitespace/punctuation artifacts from optional blanks.
    rendered = re.sub(r"\s+", " ", rendered).strip()
    rendered = re.sub(r"\s+([,.;:])", r"\1", rendered)
    rendered = re.sub(r"\(\s*\)", "", rendered)
    return rendered.strip()


def _format_value(value, field_name: str, json_schema: dict) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        return "Present" if value else "Absent"

    if isinstance(value, list):
        return ", ".join(str(v) for v in value)

    return str(value)
