from django.contrib import admin
from .models import SequenceCounter


@admin.register(SequenceCounter)
class SequenceCounterAdmin(admin.ModelAdmin):
    list_display = ("key", "period", "value", "updated_at")
    list_filter = ("key",)
    search_fields = ("key", "period")
    readonly_fields = ("value", "updated_at")
