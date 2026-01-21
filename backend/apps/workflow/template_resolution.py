"""
Template resolution utilities for workflow USG reports.
Ensures every report can resolve its template schema.
"""
from rest_framework.exceptions import ValidationError
from .models import USGReport
from apps.templates.models import TemplateVersion


def resolve_template_schema_for_report(report: USGReport) -> dict:
    """
    Resolve template schema for a USG report.
    
    Priority:
    1) If report.template_version exists, use its schema
    2) Else try to resolve from service.default_template
    3) Else raise ValidationError
    
    Args:
        report: USGReport instance
    
    Returns:
        dict: Template schema JSON
    
    Raises:
        ValidationError: If template cannot be resolved
    """
    
    # 1. Check existing template_version
    if report.template_version:
        schema = report.template_version.schema
        if schema:
            return schema
        else:
            raise ValidationError(
                f"Report has template_version {report.template_version.id} but it has no schema. "
                f"This should not happen - template version may be corrupt."
            )
    
    # 2. Try to resolve from service
    service = None
    if report.service_visit_item and report.service_visit_item.service:
        service = report.service_visit_item.service
    elif report.service_visit and report.service_visit.service:
        service = report.service_visit.service
    
    if not service:
        raise ValidationError(
            f"No template schema available for this report. "
            f"Report {report.id} has no service association and no template_version set. "
            f"Cannot resolve template."
        )
    
    # Get default template from service
    template = service.default_template
    if not template:
        raise ValidationError(
            f"No template schema available for this report. "
            f"Service '{service.code}' has no default_template configured. "
            f"Please configure a template for this service."
        )
    
    # Get latest published version
    template_version = template.versions.filter(is_published=True).order_by("-version").first()
    if not template_version:
        raise ValidationError(
            f"No template schema available for this report. "
            f"Service '{service.code}' template '{template.name}' has no published version. "
            f"Please publish at least one version of the template."
        )
    
    # Backfill the report with the resolved template_version
    report.template_version = template_version
    report.save(update_fields=["template_version"])
    
    return template_version.schema


def ensure_template_for_report(report: USGReport) -> TemplateVersion:
    """
    Ensure a report has a valid template_version set.
    If not, tries to resolve and set it.
    
    Args:
        report: USGReport instance
    
    Returns:
        TemplateVersion: The resolved template version
    
    Raises:
        ValidationError: If template cannot be resolved
    """
    if report.template_version:
        return report.template_version
    
    # Try to resolve
    service = None
    if report.service_visit_item and report.service_visit_item.service:
        service = report.service_visit_item.service
    elif report.service_visit and report.service_visit.service:
        service = report.service_visit.service
    
    if not service:
        raise ValidationError(
            f"Cannot resolve template for report {report.id}: no service association"
        )
    
    template = service.default_template
    if not template:
        raise ValidationError(
            f"Cannot resolve template for report {report.id}: "
            f"service '{service.code}' has no default_template"
        )
    
    template_version = template.versions.filter(is_published=True).order_by("-version").first()
    if not template_version:
        raise ValidationError(
            f"Cannot resolve template for report {report.id}: "
            f"template '{template.name}' has no published version"
        )
    
    # Set and save
    report.template_version = template_version
    report.save(update_fields=["template_version"])
    
    return template_version
