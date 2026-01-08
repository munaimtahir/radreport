"""
PHASE D: Dynamic organ modules mapping by study type
Maps study_type/service to list of organ modules to load
"""

# Study type to organ modules mapping
STUDY_TYPE_ORGAN_MODULES = {
    "Abdomen": [
        "Liver",
        "Gallbladder_Biliary",
        "Pancreas",
        "Spleen",
        "Kidneys",
        "Aorta",
        "IVC",
        "Ascites",
        "Other_Findings"
    ],
    "Pelvis": [
        "Uterus",
        "Endometrium",
        "Ovaries",
        "Adnexa",
        "Cul_de_sac",
        "Bladder",
        "Other_Findings"
    ],
    "KUB": [
        "Kidneys",
        "Ureters",
        "Bladder",
        "Other_Findings"
    ],
    "OB": [
        "Fetal_Presentation",
        "Fetal_Heart_Rate",
        "Placenta",
        "Amniotic_Fluid",
        "Biometry",
        "Other_Findings"
    ],
    "Doppler": [
        "Vascular_Assessment",
        "Flow_Characteristics",
        "Resistance_Indices",
        "Other_Findings"
    ],
    "Other": [
        "Findings"
    ]
}

# Controlled vocabulary for common descriptors
CONTROLLED_VOCABULARY = {
    "echogenicity": [
        "Anechoic",
        "Hypoechoic",
        "Isoechoic",
        "Hyperechoic",
        "Mixed"
    ],
    "margins": [
        "Well-defined",
        "Ill-defined",
        "Irregular",
        "Smooth",
        "Lobulated"
    ],
    "vascularity": [
        "Avascular",
        "Hypovascular",
        "Normal",
        "Hypervascular",
        "Not assessed"
    ],
    "size": [
        "Normal",
        "Enlarged",
        "Reduced",
        "Atrophic"
    ],
    "texture": [
        "Homogeneous",
        "Heterogeneous",
        "Coarse",
        "Fine"
    ]
}


def get_organ_modules_for_study_type(study_type):
    """
    Get list of organ modules for a given study type.
    
    Args:
        study_type: Study type string (e.g., "Abdomen", "Pelvis")
    
    Returns:
        List of organ module names
    """
    return STUDY_TYPE_ORGAN_MODULES.get(study_type, STUDY_TYPE_ORGAN_MODULES["Other"])


def get_controlled_vocabulary(field_type):
    """
    Get controlled vocabulary options for a field type.
    
    Args:
        field_type: Type of field (e.g., "echogenicity", "margins")
    
    Returns:
        List of vocabulary options
    """
    return CONTROLLED_VOCABULARY.get(field_type, [])


def initialize_findings_json(study_type):
    """
    Initialize findings_json structure with empty organ modules for a study type.
    
    Args:
        study_type: Study type string
    
    Returns:
        Dictionary with organ modules as keys and empty dicts as values
    """
    modules = get_organ_modules_for_study_type(study_type)
    return {module: {} for module in modules}
