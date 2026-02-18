"""
Comprehensive Role-Based Access Control (RBAC) for RIMS workflow

New Roles:
- receptionist: Can register patients, create visits
- technologist: Can perform scans, start reports, save drafts
- radiologist: Can verify, publish, return reports
- manager: Can access admin settings, backups, etc.

Legacy Roles (backward compatible):
- registration_desk / registration -> receptionist
- performance_desk / performance -> technologist
- verification_desk / verification -> radiologist
"""
from rest_framework import permissions


def _get_user_group_names(user):
    """Get lowercase group names for a user"""
    if not user or not user.is_authenticated:
        return []
    return [g.name.lower() for g in user.groups.all()]


def _has_role(user, role_names):
    """Check if user has any of the specified roles (case-insensitive)"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    group_names = _get_user_group_names(user)
    return any(name in role_names for name in group_names)


# Role name mappings (new roles + legacy compatibility)
RECEPTIONIST_ROLES = ["receptionist", "registration", "registration_desk"]
TECHNOLOGIST_ROLES = ["technologist", "performance", "performance_desk"]
RADIOLOGIST_ROLES = ["radiologist", "verification", "verification_desk"]
MANAGER_ROLES = ["manager", "admin"]

# All workflow roles
ALL_WORKFLOW_ROLES = RECEPTIONIST_ROLES + TECHNOLOGIST_ROLES + RADIOLOGIST_ROLES


class IsReceptionist(permissions.BasePermission):
    """Permission check for Receptionist role (can register patients, create visits)"""
    def has_permission(self, request, view):
        return _has_role(request.user, RECEPTIONIST_ROLES)


class IsRegistrationDesk(permissions.BasePermission):
    """Legacy alias for IsReceptionist - maintains backward compatibility"""
    def has_permission(self, request, view):
        return IsReceptionist().has_permission(request, view)


class IsTechnologist(permissions.BasePermission):
    """Permission check for Technologist role (can perform scans, start reports, save drafts)"""
    def has_permission(self, request, view):
        return _has_role(request.user, TECHNOLOGIST_ROLES)


class IsPerformanceDesk(permissions.BasePermission):
    """Legacy alias for IsTechnologist - maintains backward compatibility"""
    def has_permission(self, request, view):
        return IsTechnologist().has_permission(request, view)


class IsRadiologist(permissions.BasePermission):
    """Permission check for Radiologist role (can verify, publish, return reports)"""
    def has_permission(self, request, view):
        return _has_role(request.user, RADIOLOGIST_ROLES)


class IsVerificationDesk(permissions.BasePermission):
    """Legacy alias for IsRadiologist - maintains backward compatibility"""
    def has_permission(self, request, view):
        return IsRadiologist().has_permission(request, view)


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


class IsManager(permissions.BasePermission):
    """Permission check for Manager role (can access admin settings, backups, etc.)"""
    def has_permission(self, request, view):
        return _has_role(request.user, MANAGER_ROLES)


class IsAnyDesk(permissions.BasePermission):
    """Permission check for any workflow role (receptionist, technologist, radiologist)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return _has_role(request.user, ALL_WORKFLOW_ROLES)


# PHASE C: Granular role permissions
class IsUSGOperator(permissions.BasePermission):
    """Permission for USG operators (can start, save draft, submit)"""
    def has_permission(self, request, view):
        return IsTechnologist().has_permission(request, view)


class IsVerifier(permissions.BasePermission):
    """Permission for verifiers/radiologists (can verify, publish, return)"""
    def has_permission(self, request, view):
        return IsRadiologist().has_permission(request, view)


class IsOPDOperator(permissions.BasePermission):
    """Permission for OPD operators (can enter vitals)"""
    def has_permission(self, request, view):
        return IsTechnologist().has_permission(request, view)


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
        return IsReceptionist().has_permission(request, view)


class IsRegistrationOrVerificationDesk(permissions.BasePermission):
    """Permission check for Registration or Verification desk - allows verification users to create visits"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return IsReceptionist().has_permission(request, view) or \
               IsRadiologist().has_permission(request, view)


class IsReceptionistOrRadiologist(permissions.BasePermission):
    """Permission check for Receptionist or Radiologist - allows radiologists to create visits"""
    def has_permission(self, request, view):
        return IsRegistrationOrVerificationDesk().has_permission(request, view)
