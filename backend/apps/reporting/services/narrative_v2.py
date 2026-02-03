"""
V2 Narrative Engine for JSON schema-based templates.
Executes narrative_rules from ReportTemplateV2 to generate narrative_json.
"""
import logging
import re

logger = logging.getLogger(__name__)


def generate_narrative_v2(template_v2, values_json: dict) -> dict:
    """
    Generate narrative from V2 template rules and values.
    
    Args:
        template_v2: ReportTemplateV2 instance
        values_json: dict of field values
    
    Returns:
        dict with rendered narrative sections
    """
    narrative_rules = template_v2.narrative_rules or {}
    
    # If no rules, return empty narrative
    if not narrative_rules:
        return {}
    
    result = {}
    
    # Process sections
    sections = narrative_rules.get("sections", [])
    if sections:
        rendered_sections = []
        for section in sections:
            title = section.get("title", "")
            lines = section.get("lines", [])
            
            rendered_lines = []
            for line_template in lines:
                rendered_line = _render_template(line_template, values_json, template_v2.json_schema)
                if rendered_line:  # Only include non-empty lines
                    rendered_lines.append(rendered_line)
            
            if rendered_lines:  # Only include sections with content
                rendered_sections.append({
                    "title": title,
                    "lines": rendered_lines
                })
        
        result["sections"] = rendered_sections
    
    # Process impression
    impression_templates = narrative_rules.get("impression", [])
    if impression_templates:
        impression_lines = []
        for template in impression_templates:
            rendered = _render_template(template, values_json, template_v2.json_schema)
            if rendered:
                impression_lines.append(rendered)
        
        if impression_lines:
            result["impression"] = impression_lines
    
    return result


def _render_template(template: str, values: dict, json_schema: dict) -> str:
    """
    Render a template string by replacing {{field}} placeholders.
    
    Args:
        template: Template string with {{field}} placeholders
        values: Dict of field values
        json_schema: JSON schema for field metadata
    
    Returns:
        Rendered string, or empty string if any required field is missing/empty
    """
    # Find all {{field}} placeholders
    pattern = r'\{\{(\w+)\}\}'
    fields = re.findall(pattern, template)
    
    # Check if all fields have values
    for field in fields:
        value = values.get(field)
        if value is None or value == "" or value == []:
            # Field is missing or empty, omit this line
            return ""
    
    # Replace placeholders with formatted values
    def replace_field(match):
        field_name = match.group(1)
        value = values.get(field_name)
        return _format_value(value, field_name, json_schema)
    
    rendered = re.sub(pattern, replace_field, template)
    return rendered.strip()


def _format_value(value, field_name: str, json_schema: dict) -> str:
    """
    Format a value for display in narrative.
    
    Args:
        value: The field value
        field_name: Name of the field
        json_schema: JSON schema for type information
    
    Returns:
        Formatted string representation
    """
    if value is None:
        return ""
    
    # Get field schema
    properties = json_schema.get("properties", {})
    field_schema = properties.get(field_name, {})
    field_type = field_schema.get("type")
    
    # Boolean formatting
    if field_type == "boolean":
        if isinstance(value, bool):
            return "Present" if value else "Absent"
        # Handle string representations
        str_val = str(value).lower()
        if str_val in ("true", "1", "yes"):
            return "Present"
        elif str_val in ("false", "0", "no"):
            return "Absent"
        return str(value)
    
    # Array formatting (for enum with multiple selections)
    if isinstance(value, list):
        if not value:
            return ""
        # Join with commas
        return ", ".join(str(v) for v in value)
    
    # Default: convert to string
    return str(value)
