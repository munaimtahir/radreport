"""
V2 Narrative Engine for JSON schema-based templates.
Executes narrative_rules from ReportTemplateV2 to generate narrative_json.
Supports:
- Computed fields (safe math expressions)
- Conditional logic (if/then/else)
- Impression rule synthesis
"""
import logging
import re
import ast
import operator
import math

logger = logging.getLogger(__name__)

# --- Safe Expression Evaluator for Computed Fields ---

class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, names):
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
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
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
            left = right # Chain comparisons? Simplified here.
        return True

    def visit_Call(self, node):
        func_name = node.func.id
        if func_name not in self.functions:
            raise ValueError(f"Function {func_name} not allowed")
        args = [self.visit(arg) for arg in node.args]
        return self.functions[func_name](*args)

    def visit_Name(self, node):
        val = self.names.get(node.id)
        if val is None:
             # Try converting to float/int if possible? 
             # Or raise error? For robustness, return 0 or None? 
             # Spec: "Missing fields -> safe skip".
             # For math, returning 0 might be safer than crashing.
             return 0
        try:
            return float(val)
        except (ValueError, TypeError):
            return val

    def visit_Constant(self, node):
        return node.value

    def generic_visit(self, node):
        raise ValueError(f"Operation not allowed: {type(node).__name__}")

def safe_eval(expr, context):
    try:
        if not expr:
            return None
        node = ast.parse(expr, mode='eval')
        evaluator = SafeEvaluator(context)
        return evaluator.visit(node.body)
    except Exception as e:
        logger.warning(f"Failed to evaluate expression '{expr}': {e}")
        return None

# --- Main Engine ---

def generate_narrative_v2(template_v2, values_json: dict) -> dict:
    narrative_rules = template_v2.narrative_rules or {}

    # 1. Computed Fields
    computed_defs = narrative_rules.get("computed_fields", {})
    context_values = values_json.copy()

    for field_name, expr in computed_defs.items():
        val = safe_eval(expr, context_values)
        if val is not None:
            context_values[field_name] = val

    result = {}

    # 2. Process Sections (Conditional Narrative) with deterministic ordering
    sections_def = narrative_rules.get("sections", [])
    result["sections"] = _process_sections(sections_def, context_values, template_v2.json_schema)

    # 3. Impression Synthesis (multiple matches allowed)
    impression_rules = narrative_rules.get("impression_rules", [])
    result["impression"] = _process_impression(impression_rules, context_values, template_v2.json_schema)

    # Store computed values for reference
    computed_values = {k: context_values[k] for k in computed_defs.keys() if k in context_values}
    if computed_values:
        result["computed"] = computed_values

    return result

def _process_sections(sections_def, values, schema):
    rendered_sections = []

    for section in sections_def:
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
    """
    Process a single rule (string or dict condition).
    Returns string, list of strings, or None.
    """
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
            cond = rule["if"]
            if _evaluate_condition(cond, values):
                if "then" in rule:
                    return _process_rule(rule["then"], values, schema)
            else:
                if "else" in rule:
                    return _process_rule(rule["else"], values, schema)
        
        # Or recursive list via "rules" key
        if "rules" in rule:
             return _process_rule(rule["rules"], values, schema)
            
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

            # Explicit stop/continue semantics:
            # - `stop: true` means stop evaluation immediately
            # - `continue: false` (legacy) means stop evaluation 
            # - Otherwise, continue to next rule
            explicit_stop = bool(rule.get("stop")) or (
                "continue" in rule and rule.get("continue") is False
            )
            if explicit_stop:
                break

    return impressions

def _evaluate_condition(condition, values):
    if not condition:
        return True
    
    field = condition.get("field")
    val = values.get(field)
    
    # Operators
    if "equals" in condition:
        return val == condition["equals"]
    if "not_equals" in condition:
        return val != condition["not_equals"]
    if "gt" in condition:
        return val is not None and val > condition["gt"]
    if "gte" in condition:
        return val is not None and val >= condition["gte"]
    if "lt" in condition:
        return val is not None and val < condition["lt"]
    if "lte" in condition:
        return val is not None and val <= condition["lte"]
    if "is_empty" in condition:
        return val is None or val == "" or val == []
    if "is_not_empty" in condition:
        return val is not None and val != "" and val != []
    if "in" in condition:
        return val in condition["in"]
    if "not_in" in condition:
        return val not in condition["not_in"]
        
    return False

def _render_template(template: str, values: dict, json_schema: dict) -> str:
    # Find all {{field}} placeholders
    pattern = r"\{\{(\w+)\}\}"
    fields = re.findall(pattern, template)

    for field in fields:
        value = values.get(field)
        if value is None or value == "" or value == []:
            return ""  # Skip if any required placeholder is missing/empty

    def replace_field(match):
        field_name = match.group(1)
        value = values.get(field_name)
        return _format_value(value, field_name, json_schema)

    return re.sub(pattern, replace_field, template).strip()

def _format_value(value, field_name: str, json_schema: dict) -> str:
    if value is None:
        return ""
    
    if isinstance(value, bool):
        return "Present" if value else "Absent"
        
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
        
    return str(value)
