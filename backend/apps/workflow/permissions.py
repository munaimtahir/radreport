"""
Role-Based Access Control (RBAC) for RIMS workflow desks
"""
from rest_framework import permissions

# Desk roles
DESK_ROLES = {
    "REGISTRATION": "registration",
    "PERFORMANCE": "performance",
    "VERIFICATION": "verification",
}


class IsRegistrationDesk(permissions.BasePermission):
    """Permission check for Registration desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        # Check if user has registration role (via groups or user profile)
        return request.user.groups.filter(name="Registration").exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) == DESK_ROLES["REGISTRATION"])


class IsPerformanceDesk(permissions.BasePermission):
    """Permission check for Performance desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="Performance").exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) == DESK_ROLES["PERFORMANCE"])


class IsVerificationDesk(permissions.BasePermission):
    """Permission check for Verification desk"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="Verification").exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) == DESK_ROLES["VERIFICATION"])


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
        # For MVP, allow any authenticated user
        # In production, check for specific desk roles
        return True
