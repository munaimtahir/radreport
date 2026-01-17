from django.contrib import admin

from .models import ConsultantProfile, ConsultantBillingRule, ConsultantSettlement, ConsultantSettlementLine


@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "is_active", "user", "created_at")
    list_filter = ("is_active",)
    search_fields = ("display_name", "user__username")


@admin.register(ConsultantBillingRule)
class ConsultantBillingRuleAdmin(admin.ModelAdmin):
    list_display = ("consultant", "rule_type", "consultant_percent", "is_active", "active_from")
    list_filter = ("rule_type", "is_active")
    search_fields = ("consultant__display_name",)


class ConsultantSettlementLineInline(admin.TabularInline):
    model = ConsultantSettlementLine
    extra = 0
    readonly_fields = (
        "service_item",
        "item_amount_snapshot",
        "paid_amount_snapshot",
        "consultant_share_snapshot",
        "clinic_share_snapshot",
        "metadata",
        "created_at",
    )
    can_delete = False


@admin.register(ConsultantSettlement)
class ConsultantSettlementAdmin(admin.ModelAdmin):
    list_display = ("consultant", "date_from", "date_to", "gross_collected", "status", "finalized_at")
    list_filter = ("status", "consultant")
    search_fields = ("consultant__display_name",)
    inlines = [ConsultantSettlementLineInline]
    readonly_fields = ("gross_collected", "net_payable", "clinic_share", "finalized_at", "finalized_by")


@admin.register(ConsultantSettlementLine)
class ConsultantSettlementLineAdmin(admin.ModelAdmin):
    list_display = ("settlement", "service_item", "paid_amount_snapshot", "consultant_share_snapshot")
    search_fields = ("settlement__consultant__display_name", "service_item__service_name_snapshot")
