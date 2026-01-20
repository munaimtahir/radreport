from .models import UsgStudy, UsgTemplate, UsgServiceProfile
from rest_framework.exceptions import ValidationError

def resolve_template_for_report(report: UsgStudy):
    """
    Resolve and attach a template to the report (UsgStudy).
    
    Priority:
    1) If report.template_snapshot exists, return it (already resolved).
    2) Else if report.template (FK) exists, use that to generate snapshot.
    3) Else resolve mapping by report.service_code.
    
    If resolved (case 2 or 3), updates the report instance and saves it.
    If fails, raises ValidationError.
    
    Returns:
        dict: The template schema JSON.
    """
    
    # 1. Check existing snapshot
    if report.template_snapshot:
        return report.template_snapshot
        
    # 2. Check FK
    if report.template:
        # Load from FK
        schema = report.template.schema_json
        # Save snapshot for future immutability
        report.template_snapshot = schema
        report.save(update_fields=['template_snapshot'])
        return schema
        
    # 3. Resolve mapping
    if not report.service_code:
        raise ValidationError("Report has no service_code, cannot resolve template.")
        
    profile = UsgServiceProfile.objects.select_related('template').filter(
        service_code=report.service_code
    ).first()
    
    if not profile:
        raise ValidationError(
            f"No template schema available for this report. "
            f"No mapping found for service_code='{report.service_code}'"
        )
        
    # Attach and save
    report.template = profile.template
    report.template_snapshot = profile.template.schema_json
    report.save(update_fields=['template', 'template_snapshot'])
    
    return report.template_snapshot
