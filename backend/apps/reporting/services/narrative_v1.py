import logging
from django.utils import timezone
from apps.reporting.models import ReportInstance, ReportValue, ReportParameter

logger = logging.getLogger(__name__)

def generate_report_narrative(report_instance_id: str) -> dict:
    """
    Deterministically generates the narrative text for a ReportInstance.
    
    Returns:
    {
        "findings_text": "...",
        "impression_text": "...",
        "limitations_text": "...",
        "version": "v1"
    }
    """
    
    try:
        instance = ReportInstance.objects.select_related('profile').get(id=report_instance_id)
        profile = instance.profile
    except ReportInstance.DoesNotExist:
        logger.error(f"ReportInstance {report_instance_id} not found.")
        raise ValueError("Report instance not found")

    if not profile.enable_narrative:
        return {
            "findings_text": "",
            "impression_text": "",
            "limitations_text": "",
            "version": "v1"
        }

    # Fetch parameters and values
    parameters = profile.parameters.all()
    # Create a map of param_id -> ReportValue object
    # Using select_related/prefetch might be better if many values, but simplified here
    values_qs = ReportValue.objects.filter(report=instance)
    values_map = {v.parameter_id: v for v in values_qs}

    # Containers for output
    sections_map = {} # section_name -> list of sentences
    impression_lines = []
    limitation_lines = []
    
    # Process parameters in order
    sorted_params = sorted(parameters, key=lambda p: (p.section, p.order))
    
    # Keep track of section order as we encounter them
    section_order = []

    for param in sorted_params:
        role = param.narrative_role
        if role == "ignore":
            continue

        val_obj = values_map.get(param.id)
        raw_val = val_obj.value if val_obj else None
        
        # Omission Logic
        # Default omits: None, "", "na", [], False (if boolean?) - User said "na", "", null, [], false
        # We need to parse the raw_val to check these conditions properly especially for JSON types if they exist
        # ReportValue.value is TextField.
        
        # 1. format the value for display
        display_val, is_empty_equivalent = _format_value(param, raw_val)

        # 2. Check explicit omission config
        omit_list = param.omit_if_values
        if omit_list is None:
             # Default omission rules:
             # If is_empty_equivalent is true, we omit.
             if is_empty_equivalent:
                 continue
        else:
            # Explicit omission list
            # We check if the raw_value (or some normalized form) is in the omit list.
            # Ideally we match against raw string or parsed json. 
            # For simplicity, we check if raw_val matches, or if it is "empty" and null is in list, etc.
            # But the requirement says: "If value is missing OR value in omit_if_values => skip sentence."
            # "Default omit_if_values should treat: "na", "", null, [], false as omit unless parameter explicitly opts out."
            
            # This implies if omit_list IS provided, we ONLY use that list + "missing".
            # If value is completely missing (None/null database side), it's always skipped unless maybe default provided?
            # Let's assume if raw_val is None, it is skipped regardless, unless we want to report "Not recorded"? 
            # Usually strict reporting skips empty fields.
            
            if raw_val is None:
                continue

            # Check exact match in list
            # We might need to cast raw_val to type for comparison? 
            # e.g. boolean param "false" vs False in JSON.
            if _is_in_omit_list(raw_val, omit_list, param.parameter_type):
                continue

        # 3. Build sentence
        sentence = _build_sentence(param, display_val)
        
        # 4. Slot into roles
        if role == "finding":
            if param.section not in sections_map:
                sections_map[param.section] = []
                section_order.append(param.section)
            sections_map[param.section].append(sentence)
        elif role == "impression_hint":
            impression_lines.append(sentence)
        elif role == "limitation_hint":
            limitation_lines.append(sentence)

    # Assemble Findings Text
    findings_parts = []
    for section in section_order:
        sentences = sections_map.get(section, [])
        if not sentences:
            continue
        findings_parts.append(f"{section}:")
        for s in sentences:
            findings_parts.append(f"- {s}")
        findings_parts.append("") # Spacer
    
    findings_text = "\n".join(findings_parts).strip()
    impression_text = "\n".join(impression_lines).strip()
    limitations_text = "\n".join(limitation_lines).strip()

    return {
        "findings_text": findings_text,
        "impression_text": impression_text,
        "limitations_text": limitations_text,
        "version": "v1"
    }

def _format_value(param, raw_val):
    """
    Returns (display_string, is_empty_equivalent)
    """
    if raw_val is None:
        return "", True
    
    ptype = param.parameter_type
    
    if ptype == "boolean":
        # Expecting "true"/"false" or python bool
        lower = str(raw_val).lower()
        if lower in ("true", "1", "yes"):
            return "Yes", False
        if lower in ("false", "0", "no"):
            return "No", True # Default rule treats false as omit often, but we handle that in caller. 
            # Actually, is_empty_equivalent is for DEFAULT omit check. 
            # Requirement: "Default omit_if_values should treat... false as omit"
            # So returning True here is correct for default behavior.
            
        return raw_val, False

    if ptype in ("short_text", "long_text"):
        s = str(raw_val).strip()
        if s == "":
            return "", True
        if s.lower() == "na":
            return s, True # Treating "na" as empty for default omit
        return s, False

    if ptype == "number":
        # Check for empty string
        s = str(raw_val).strip()
        if s == "":
             return "", True
        return s, False

    if ptype == "dropdown":
        # Try to find option label
        # raw_val is the 'value' stored.
        # We need to look up corresponding Option.label
        # This is expensive N+1 if we query every time. 
        # Ideally, we should have pre-fetched options or use the value itself if label missing.
        # For Optimization: caller could prefetch options. 
        # Here we will do a quick lookup (cached by Django if prefetched, otherwise hit DB).
        # To avoid N queries, we can try to rely on the fact that for standard Reports,
        # usually labels are what we want.
        # Let's do a lookup.
        
        option = param.options.filter(value=raw_val).first()
        label = option.label if option else raw_val
        
        if raw_val == "": return "", True
        if str(raw_val).lower() == "na": return label, True
        
        return label, False

    if ptype == "checklist":
        # raw_val is likely JSON list or comma strings. 
        # Let's assume it handles Python list if ReportValue parsing logic existed, 
        # but ReportValue.value is TextField.
        # We assume it's stored as serialized JSON or something standard.
        # If it's just a comma string, we split. 
        # Let's assume simple string for now or try to parse JSON.
        import json
        selected_values = []
        try:
            selected_values = json.loads(raw_val)
            if not isinstance(selected_values, list):
                if selected_values: selected_values = [str(selected_values)]
                else: selected_values = []
        except:
            if raw_val: selected_values = [raw_val]
        
        if not selected_values:
            return "", True
            
        # Map to labels
        # Bulk fetch options for this param
        options = {o.value: o.label for o in param.options.all()}
        labels = [options.get(str(v), str(v)) for v in selected_values]
        
        joiner = param.join_label if param.join_label else ", "
        return joiner.join(labels), False
        
    return str(raw_val), False

def _is_in_omit_list(raw_val, omit_list, ptype):
    """
    Check if raw_val qualifies for omission based on explicit omit_list.
    """
    if not isinstance(omit_list, list):
        return False
        
    # Check for direct existence
    if raw_val in omit_list:
        return True
        
    # Type specific checks
    if ptype == "boolean":
        lower = str(raw_val).lower()
        is_true = lower in ("true", "1", "yes")
        is_false = lower in ("false", "0", "no")
        
        if is_false and False in omit_list: return True
        if is_true and True in omit_list: return True
        if raw_val == "false" and "false" in omit_list: return True

    return False

def _build_sentence(param, display_val):
    if param.sentence_template:
        # {name}, {value}, {unit}, {section}
        unit_str = param.unit if param.unit else ""
        text = param.sentence_template.format(
            name=param.name,
            value=display_val,
            unit=unit_str,
            section=param.section
        )
        return text
    else:
        # Default: "{name}: {value}{unit}."
        unit_str = param.unit if param.unit else ""
        return f"{param.name}: {display_val}{unit_str}."

