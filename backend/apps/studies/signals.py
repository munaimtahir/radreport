from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Study
from apps.reporting.models import Report
from apps.templates.models import TemplateVersion

@receiver(post_save, sender=Study)
def create_draft_report(sender, instance, created, **kwargs):
    """Auto-create a draft report when a study is created, if service has a default template"""
    if created and not hasattr(instance, 'report'):
        # Try to get the default template from the service
        default_template = instance.service.default_template
        if default_template:
            # Get the latest published version of the template
            latest_version = default_template.versions.filter(is_published=True).order_by('-version').first()
            if latest_version:
                Report.objects.create(
                    study=instance,
                    template_version=latest_version,
                    status='draft'
                )
