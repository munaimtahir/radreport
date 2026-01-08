"""
PHASE C: Transition Service - Enforces valid state transitions per department item type.

This module provides a centralized service for validating and executing workflow transitions.
All transitions must go through this service to ensure:
- Valid state transitions
- Role-based permissions
- Audit logging
- Timestamp updates
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from .models import ServiceVisitItem, StatusAuditLog, ServiceVisit

# PHASE C: Define allowed transitions per department/item type
USG_TRANSITIONS = {
    "REGISTERED": ["IN_PROGRESS"],
    "IN_PROGRESS": ["PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION"],
    "PENDING_VERIFICATION": ["PUBLISHED", "RETURNED_FOR_CORRECTION"],
    "RETURNED_FOR_CORRECTION": ["IN_PROGRESS"],
    "PUBLISHED": [],  # Terminal state
    "CANCELLED": [],  # Terminal state
}

OPD_TRANSITIONS = {
    "REGISTERED": ["IN_PROGRESS"],
    "IN_PROGRESS": ["FINALIZED", "PENDING_VERIFICATION"],  # PENDING_VERIFICATION optional if doctor verify
    "FINALIZED": ["PUBLISHED"],
    "PENDING_VERIFICATION": ["FINALIZED", "PUBLISHED"],  # If verification step exists
    "PUBLISHED": [],  # Terminal state
    "CANCELLED": [],  # Terminal state
}

# PHASE C: Role-based permissions for transitions
TRANSITION_PERMISSIONS = {
    # USG transitions
    ("USG", "REGISTERED", "IN_PROGRESS"): ["USG_OPERATOR", "PERFORMANCE", "ADMIN"],
    ("USG", "IN_PROGRESS", "PENDING_VERIFICATION"): ["USG_OPERATOR", "PERFORMANCE", "ADMIN"],
    ("USG", "PENDING_VERIFICATION", "PUBLISHED"): ["VERIFIER", "VERIFICATION", "ADMIN"],
    ("USG", "PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION"): ["VERIFIER", "VERIFICATION", "ADMIN"],
    ("USG", "RETURNED_FOR_CORRECTION", "IN_PROGRESS"): ["USG_OPERATOR", "PERFORMANCE", "ADMIN"],
    
    # OPD transitions
    ("OPD", "REGISTERED", "IN_PROGRESS"): ["OPD_OPERATOR", "PERFORMANCE", "ADMIN"],
    ("OPD", "IN_PROGRESS", "FINALIZED"): ["DOCTOR", "ADMIN"],
    ("OPD", "IN_PROGRESS", "PENDING_VERIFICATION"): ["OPD_OPERATOR", "PERFORMANCE", "ADMIN"],  # Optional
    ("OPD", "FINALIZED", "PUBLISHED"): ["DOCTOR", "ADMIN"],
    ("OPD", "PENDING_VERIFICATION", "PUBLISHED"): ["DOCTOR", "ADMIN"],
    
    # Common transitions
    ("*", "*", "CANCELLED"): ["ADMIN"],  # Only admin can cancel
}


def get_user_roles(user):
    """
    Get user roles from groups or profile.
    Returns list of role strings.
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_superuser:
        return ["ADMIN"]
    
    roles = []
    
    # Check Django groups
    group_names = user.groups.values_list('name', flat=True)
    for group_name in group_names:
        group_upper = group_name.upper()
        if group_upper in ["REGISTRATION", "PERFORMANCE", "VERIFICATION", "ADMIN"]:
            roles.append(group_upper)
        # Map group names to role names
        if group_upper == "PERFORMANCE":
            roles.extend(["USG_OPERATOR", "OPD_OPERATOR"])
        if group_upper == "VERIFICATION":
            roles.append("VERIFIER")
    
    # Check user profile if exists
    if hasattr(user, 'profile'):
        desk_role = getattr(user.profile, 'desk_role', None)
        if desk_role:
            roles.append(desk_role.upper())
    
    return list(set(roles))  # Remove duplicates


def can_transition(user, department, from_status, to_status):
    """
    Check if user has permission to perform transition.
    
    Args:
        user: User object
        department: "USG" or "OPD"
        from_status: Current status
        to_status: Target status
    
    Returns:
        bool: True if allowed, False otherwise
    """
    user_roles = get_user_roles(user)
    
    # Check specific department transition
    key = (department, from_status, to_status)
    if key in TRANSITION_PERMISSIONS:
        allowed_roles = TRANSITION_PERMISSIONS[key]
        return any(role in user_roles for role in allowed_roles)
    
    # Check wildcard (e.g., cancellation)
    wildcard_key = ("*", "*", to_status)
    if wildcard_key in TRANSITION_PERMISSIONS:
        allowed_roles = TRANSITION_PERMISSIONS[wildcard_key]
        return any(role in user_roles for role in allowed_roles)
    
    # Default: deny if not explicitly allowed
    return False


def get_allowed_transitions(department, current_status):
    """
    Get list of allowed transitions for a department and status.
    
    Args:
        department: "USG" or "OPD"
        current_status: Current status string
    
    Returns:
        list: List of allowed target statuses
    """
    if department == "USG":
        transitions = USG_TRANSITIONS
    elif department == "OPD":
        transitions = OPD_TRANSITIONS
    else:
        return []
    
    return transitions.get(current_status, [])


def transition_item_status(item, to_status, user, reason=None):
    """
    PHASE C: Execute a status transition for a ServiceVisitItem.
    
    This is the ONLY way to change item status - enforces:
    - Valid transitions
    - Role permissions
    - Audit logging
    - Timestamp updates
    - Visit status derivation
    
    Args:
        item: ServiceVisitItem instance
        to_status: Target status string
        user: User performing the transition
        reason: Optional reason (required for RETURNED)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    
    Raises:
        ValidationError: If transition is invalid
        PermissionDenied: If user lacks permission
    """
    from_status = item.status
    department = item.department_snapshot
    
    # Validate transition is allowed
    allowed = get_allowed_transitions(department, from_status)
    if to_status not in allowed:
        raise ValidationError(
            f"Invalid transition for {department} item: {from_status} -> {to_status}. "
            f"Allowed: {allowed}"
        )
    
    # Check permissions
    if not can_transition(user, department, from_status, to_status):
        raise PermissionDenied(
            f"User {user.username} does not have permission to transition "
            f"{department} item from {from_status} to {to_status}"
        )
    
    # Require reason for RETURNED transitions
    if to_status == "RETURNED_FOR_CORRECTION" and not reason:
        raise ValidationError("Reason is required when returning item for correction")
    
    # Execute transition
    with transaction.atomic():
        # Update item status
        item.status = to_status
        
        # Update timestamps based on transition
        now = timezone.now()
        if to_status == "IN_PROGRESS" and not item.started_at:
            item.started_at = now
        elif to_status == "PENDING_VERIFICATION" and not item.submitted_at:
            item.submitted_at = now
        elif to_status == "PUBLISHED" and not item.published_at:
            item.published_at = now
        
        item.save()
        
        # Create audit log entry
        StatusAuditLog.objects.create(
            service_visit_item=item,
            service_visit=item.service_visit,  # Keep for backward compatibility
            from_status=from_status,
            to_status=to_status,
            reason=reason or "",
            changed_by=user,
        )
        
        # Update derived visit status
        item.service_visit.update_derived_status()
    
    return True, None
