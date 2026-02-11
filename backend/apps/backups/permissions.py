from rest_framework.permissions import BasePermission


class IsBackupManager(BasePermission):
    message = "Backup manager access required"

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        groups = set(user.groups.values_list("name", flat=True))
        return bool(groups.intersection({"manager", "admin"}))


class IsBackupRestoreSuperuser(BasePermission):
    message = "Superuser access required for restore"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
