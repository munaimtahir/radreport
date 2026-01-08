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


# PHASE C: Granular role permissions
class IsUSGOperator(permissions.BasePermission):
    """Permission for USG operators (can start, save draft, submit)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["Performance", "USG Operator"]).exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) in ["performance", "usg_operator"])


class IsVerifier(permissions.BasePermission):
    """Permission for verifiers/radiologists (can verify, publish, return)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["Verification", "Radiologist"]).exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) in ["verification", "verifier"])


class IsOPDOperator(permissions.BasePermission):
    """Permission for OPD operators (can enter vitals)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["Performance", "OPD Operator"]).exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) in ["performance", "opd_operator"])


class IsDoctor(permissions.BasePermission):
    """Permission for doctors (can finalize and publish OPD)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["Doctor", "Consultant"]).exists() or \
               (hasattr(request.user, 'profile') and getattr(request.user.profile, 'desk_role', None) in ["doctor", "consultant"])


class IsReception(permissions.BasePermission):
    """Permission for reception desk (can register, cannot edit clinical content)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return IsRegistrationDesk().has_permission(request, view)
