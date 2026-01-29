from django.contrib import admin


class HiddenFromAdminIndexModelAdmin(admin.ModelAdmin):
    """
    Hide a model from the admin index/app list while keeping it registered.
    """

    def has_module_permission(self, _request):
        return False
