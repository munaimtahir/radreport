"""
PHASE C: Role-Based Access Control (RBAC) for RIMS workflow desks

Roles:
- RECEPTION: Registration desk only
- USG_OPERATOR: Can work on USG items (start, save draft, submit)
- VERIFIER: Can verify and publish USG reports
- OPD_OPERATOR: Can work on OPD vitals
- DOCTOR: Can finalize and publish OPD consultations
- ADMIN: Full access
"""
from rest_framework import permissions

# Desk roles (canonical Django group names)
# Note: Django admin may create groups as "Registration", "Performance", "Verification"
# or "registration_desk", "performance_desk", "verification_desk"
# Backend checks for both variations (case-insensitive)
DESK_ROLES = {
    "REGISTRATION": "registration_desk",
    "PERFORMANCE": "performance_desk",
    "VERIFICATION": "verification_desk",
}

# Alternative group names that Django admin might create
DESK_ROLES_ALT = {
    "REGISTRATION": ["Registration", "registration", "registration_desk"],
    "PERFORMANCE": ["Performance", "performance", "performance_desk"],
    "VERIFICATION": ["Verification", "verification", "verification_desk"],
}


class IsRegistrationDesk(permissions.BasePermission):
    """Permission check for Registration desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        # Check for any variation of registration group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["registration", "registration_desk"] for name in group_names)


class IsPerformanceDesk(permissions.BasePermission):
    """Permission check for Performance desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        # Check for any variation of performance group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["performance", "performance_desk"] for name in group_names)


class IsVerificationDesk(permissions.BasePermission):
    """Permission check for Verification desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        # Check for any variation of verification group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["verification", "verification_desk"] for name in group_names)


class IsRegistrationOrPerformanceDesk(permissions.BasePermission):
    """Permission check for Registration or Performance desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        return IsRegistrationDesk().has_permission(request, view) or \
               IsPerformanceDesk().has_permission(request, view)


class IsPerformanceOrVerificationDesk(permissions.BasePermission):
    """Permission check for Performance or Verification desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        return IsPerformanceDesk().has_permission(request, view) or \
               IsVerificationDesk().has_permission(request, view)


class IsAnyDesk(permissions.BasePermission):
    """Permission check for any desk role - allows any authenticated user for MVP"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Check for any desk group variation (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        desk_groups = ["registration", "registration_desk", "performance", "performance_desk", 
                      "verification", "verification_desk"]
        return any(name in desk_groups for name in group_names)


# PHASE C: Granular role permissions
class IsUSGOperator(permissions.BasePermission):
    """Permission for USG operators (can start, save draft, submit)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Check for any variation of performance group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["performance", "performance_desk"] for name in group_names)


class IsVerifier(permissions.BasePermission):
    """Permission for verifiers/radiologists (can verify, publish, return)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Check for any variation of verification group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["verification", "verification_desk"] for name in group_names)


class IsOPDOperator(permissions.BasePermission):
    """Permission for OPD operators (can enter vitals)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Check for any variation of performance group name (case-insensitive)
        group_names = [g.name.lower() for g in request.user.groups.all()]
        return any(name in ["performance", "performance_desk"] for name in group_names)


class IsDoctor(permissions.BasePermission):
    """
    Permission for doctors (can finalize and publish OPD consultations).
    
    NOTE: This permission requires a 'doctor' Django group which is NOT created by
    the seed_roles_phase3 management command. The 'doctor' group is part of the OPD
    workflow (out of scope for Phase 3 USG workflow) and must be created separately
    if OPD functionality is needed.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="doctor").exists()


class IsReception(permissions.BasePermission):
    """Permission for reception desk (can register, cannot edit clinical content)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return IsRegistrationDesk().has_permission(request, view)


class IsRegistrationOrVerificationDesk(permissions.BasePermission):
    """Permission check for Registration or Verification desk - allows verification users to create visits"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        return IsRegistrationDesk().has_permission(request, view) or \
               IsVerificationDesk().has_permission(request, view)
