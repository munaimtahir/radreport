"""
Deterministic narrative renderer for USG reports.
Version: usg_renderer_v1

Rules:
- Process sections in fixed schema order
- Skip fields marked as is_not_applicable
- Skip empty/null fields
- If a section has no printable fields, skip entire section
- Output format: section headings with narrative sentences
"""


def render_usg_report(template_schema, field_values_dict):
    """
    Generate deterministic narrative text from template schema and field values.
    
    Args:
        template_schema: dict - The template schema JSON
        field_values_dict: dict - {field_key: {'value_json': ..., 'is_not_applicable': bool}}
    
    Returns:
        str - The rendered narrative text
    """
    sections = template_schema.get('sections', [])
    output_lines = []
    
    for section in sections:
        section_key = section.get('section_key')
        section_title = section.get('title')
        fields = section.get('fields', [])
        
        # Collect printable lines for this section
        section_lines = []
        
        for field in fields:
            field_key = field.get('field_key')
            field_label = field.get('label', '')
            field_type = field.get('type')
            
            # Get field value data
            field_data = field_values_dict.get(field_key, {})
            is_na = field_data.get('is_not_applicable', False)
            value = field_data.get('value_json')
            
            # Skip if NA or empty
            if is_na:
                continue
            if value is None or value == '' or value == [] or value == {}:
                continue
            
            # Render based on type
            rendered_text = _render_field(field, value)
            if rendered_text:
                section_lines.append(rendered_text)
        
        # Only add section if it has content
        if section_lines:
            output_lines.append(f"\n{section_title}:")
            output_lines.extend(section_lines)
    
    return '\n'.join(output_lines).strip()


def _render_field(field, value):
    """
    Render a single field value to narrative text.
    
    Args:
        field: dict - Field definition from template
        value: any - The field value
    
    Returns:
        str - Rendered text or empty string
    """
    field_type = field.get('type')
    field_label = field.get('label', '')
    options = field.get('options', [])
    
    if field_type == 'text':
        # Text field: just return the text
        if isinstance(value, str) and value.strip():
            return value.strip()
        return ''
    
    elif field_type == 'number':
        # Number field: render with label
        if isinstance(value, (int, float)) and value != 0:
            return f"{field_label}: {value}"
        return ''
    
    elif field_type == 'single_choice':
        # Single choice: find the label for the value
        if isinstance(value, str):
            label = _get_option_label(value, options)
            if label:
                return f"{field_label}: {label}"
        return ''
    
    elif field_type == 'multi_choice':
        # Multi-choice: join multiple labels
        if isinstance(value, list) and value:
            labels = [_get_option_label(v, options) for v in value]
            labels = [l for l in labels if l]  # Filter out empty
            if labels:
                return f"{field_label}: {', '.join(labels)}"
        return ''
    
    return ''


def _get_option_label(value, options):
    """Get the label for an option value"""
    for opt in options:
        if opt.get('value') == value:
            return opt.get('label', value)
    return value  # Fallback to value if label not found


def render_usg_report_with_metadata(template_schema, field_values_dict, study, patient):
    """
    Render full report with patient metadata and narrative.
    
    Args:
        template_schema: dict - The template schema
        field_values_dict: dict - Field values
        study: UsgStudy - The study instance
        patient: Patient - The patient instance
    
    Returns:
        str - Full report text with headers
    """
    lines = []
    
    # Patient info header
    lines.append("ULTRASOUND REPORT")
    lines.append("=" * 50)
    lines.append(f"Patient: {patient.name}")
    lines.append(f"MR Number: {patient.mrn}")
    if patient.age:
        lines.append(f"Age: {patient.age}")
    if patient.gender:
        lines.append(f"Gender: {patient.gender}")
    lines.append(f"Visit: {study.visit.visit_number}")
    lines.append(f"Service: {study.service_code}")
    lines.append(f"Date: {study.created_at.strftime('%Y-%m-%d')}")
    lines.append("=" * 50)
    lines.append("")
    
    # Narrative body
    narrative = render_usg_report(template_schema, field_values_dict)
    lines.append(narrative)
    
    return '\n'.join(lines)
