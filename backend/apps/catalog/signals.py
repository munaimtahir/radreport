"""
Audit logging signals for Service model
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Service
from apps.audit.models import AuditLog

# Store original values before save
_original_values = {}

@receiver(pre_save, sender=Service)
def service_pre_save(sender, instance, **kwargs):
    """Store original values before save"""
    if instance.pk:
        try:
            original = Service.objects.get(pk=instance.pk)
            _original_values[instance.pk] = {
                'price': original.price,
                'code': original.code,
                'name': original.name,
                'category': original.category,
                'is_active': original.is_active,
            }
        except Service.DoesNotExist:
            pass

@receiver(post_save, sender=Service)
def service_post_save(sender, instance, created, **kwargs):
    """Log service changes to audit log"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Try to get user from thread local (set by API views)
    user = getattr(instance, '_current_user', None)
    
    if created:
        AuditLog.objects.create(
            actor=user,
            action="service.created",
            entity_type="Service",
            entity_id=str(instance.id),
            meta={
                "code": instance.code,
                "name": instance.name,
                "category": instance.category,
                "price": str(instance.price),
                "modality": instance.modality.code if instance.modality else None,
            }
        )
    else:
        # Check what changed
        original = _original_values.get(instance.pk, {})
        changes = {}
        
        if original.get('price') != instance.price:
            changes['price'] = {'old': str(original.get('price')), 'new': str(instance.price)}
        if original.get('code') != instance.code:
            changes['code'] = {'old': original.get('code'), 'new': instance.code}
        if original.get('name') != instance.name:
            changes['name'] = {'old': original.get('name'), 'new': instance.name}
        if original.get('category') != instance.category:
            changes['category'] = {'old': original.get('category'), 'new': instance.category}
        if original.get('is_active') != instance.is_active:
            changes['is_active'] = {'old': original.get('is_active'), 'new': instance.is_active}
        
        if changes:
            AuditLog.objects.create(
                actor=user,
                action="service.updated",
                entity_type="Service",
                entity_id=str(instance.id),
                meta={
                    "code": instance.code,
                    "changes": changes,
                }
            )
        
        # Clean up
        if instance.pk in _original_values:
            del _original_values[instance.pk]
