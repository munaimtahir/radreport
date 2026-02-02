import logging
from django.utils import timezone
from apps.reporting.models import ReportInstance, ReportValue, ReportParameter

logger = logging.getLogger(__name__)

def generate_report_narrative(report_instance_id: str) -> dict:
    """
    Deterministically generates the narrative text for a ReportInstance.
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

    # Fetch both legacy parameters and library links
    legacy_params = list(profile.parameters.all())
    library_links = list(profile.library_links.select_related('library_item').all())

    # Fetch values
    values_qs = ReportValue.objects.filter(report=instance)
    values_map_legacy = {str(v.parameter_id): v for v in values_qs if v.parameter_id}
    values_map_links = {str(v.profile_link_id): v for v in values_qs if v.profile_link_id}

    # Normalize all into a common "narrative item" object
    items = []
    
    for p in legacy_params:
        items.append({
            "id": str(p.id),
            "name": p.name,
            "section": p.section,
            "order": p.order,
            "type": p.parameter_type,
            "unit": p.unit,
            "sentence_template": p.sentence_template,
            "narrative_role": p.narrative_role,
            "omit_if_values": p.omit_if_values,
            "join_label": p.join_label,
            "options_qs": p.options, # RelatedManager
            "raw_value": values_map_legacy.get(str(p.id)).value if values_map_legacy.get(str(p.id)) else None
        })

    for link in library_links:
        lib = link.library_item
        # Merge overrides
        overrides = link.overrides_json or {}
        items.append({
            "id": str(link.id),
            "name": lib.name,
            "section": link.section,
            "order": link.order,
            "type": lib.parameter_type,
            "unit": overrides.get("unit", lib.unit),
            "sentence_template": overrides.get("sentence_template", lib.default_sentence_template),
            "narrative_role": overrides.get("narrative_role", lib.default_narrative_role),
            "omit_if_values": overrides.get("omit_if_values", lib.default_omit_if_values),
            "join_label": overrides.get("join_label", lib.default_join_label),
            "lib_options": lib.default_options_json,
            "raw_value": values_map_links.get(str(link.id)).value if values_map_links.get(str(link.id)) else None
        })

    # Containers for output
    sections_map = {} 
    impression_lines = []
    limitation_lines = []
    
    # Process items in order
    sorted_items = sorted(items, key=lambda i: (i["section"], i["order"]))
    
    # Keep track of section order as we encounter them
    section_order = []

    for item in sorted_items:
        role = item["narrative_role"]
        if role == "ignore":
            continue

        raw_val = item["raw_value"]
        
        # 1. format the value for display
        display_val, is_empty_equivalent = _format_value_enhanced(item, raw_val)

        # 2. Check omission
        omit_list = item["omit_if_values"]
        if omit_list is None:
             if is_empty_equivalent:
                 continue
        else:
            if raw_val is None:
                continue
            if _is_in_omit_list(raw_val, omit_list, item["type"]):
                continue

        # 3. Build sentence
        sentence = _build_sentence_enhanced(item, display_val)
        
        if not sentence:
            continue

        # 4. Slot into roles
        if role == "finding":
            section = item["section"]
            if section not in sections_map:
                sections_map[section] = []
                section_order.append(section)
            sections_map[section].append(sentence)
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

def _format_value_enhanced(item, raw_val):
    """
    Returns (display_string, is_empty_equivalent)
    """
    if raw_val is None:
        return "", True
    
    ptype = item["type"]
    
    if ptype == "boolean":
        # Expecting "true"/"false" or python bool
        lower = str(raw_val).lower()
        if lower in ("true", "1", "yes"):
            return "Yes", False
        if lower in ("false", "0", "no"):
            return "No", True
        return raw_val, False

    if ptype in ("short_text", "long_text", "number"):
        s = str(raw_val).strip()
        if s == "" or s.lower() == "na":
            return s, True
        return s, False

    if ptype == "dropdown":
        if raw_val == "" or str(raw_val).lower() == "na":
            return str(raw_val), True
            
        label = raw_val
        if item.get("options_qs"):
             opt = item["options_qs"].filter(value=raw_val).first()
             if opt: label = opt.label
        elif item.get("lib_options"):
             for lo in item["lib_options"]:
                 if str(lo.get("value")) == str(raw_val):
                     label = lo.get("label", raw_val)
                     break
        return label, False

    if ptype == "checklist":
        import json
        selected_values = []
        try:
            selected_values = json.loads(raw_val)
            if not isinstance(selected_values, list):
                selected_values = [str(selected_values)] if selected_values else []
        except:
            selected_values = [raw_val] if raw_val else []
        
        if not selected_values:
            return "", True
            
        labels = []
        if item.get("options_qs"):
            opts_map = {o.value: o.label for o in item["options_qs"].all()}
            labels = [opts_map.get(str(v), str(v)) for v in selected_values]
        elif item.get("lib_options"):
            opts_map = {str(lo.get("value")): lo.get("label") for lo in item["lib_options"]}
            labels = [opts_map.get(str(v), str(v)) for v in selected_values]
        else:
            labels = [str(v) for v in selected_values]
        
        joiner = item["join_label"] if item["join_label"] else ", "
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
        if lower in ("false", "0", "no") and (False in omit_list or "false" in omit_list): return True
        if lower in ("true", "1", "yes") and (True in omit_list or "true" in omit_list): return True

    return False

def _build_sentence_enhanced(item, display_val):
    template = item["sentence_template"]
    if not template:
        unit_str = item["unit"] if item["unit"] else ""
        return f"{item['name']}: {display_val}{unit_str}."
    
    try:
        return template.format(
            name=item["name"],
            value=display_val,
            unit=item["unit"] or "",
            section=item["section"]
        )
    except Exception as e:
        logger.error(f"Formatting error in template '{template}' for item '{item['name']}': {e}")
        return f"{item['name']}: {display_val}"
