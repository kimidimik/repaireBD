from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from repairs.models import Device, Repair, RepairPartUsage


STATUS_COLORS = {
    Repair.Status.NEW: "#9ca3af",
    Repair.Status.AWAITING_PARTS: "#fb923c",
    Repair.Status.IN_PROGRESS: "#facc15",
    Repair.Status.COMPLETED: "#22c55e",
    Repair.Status.CLOSED: "#111827",
}

DIFFICULTY_COLORS = {
    Repair.Difficulty.TEST: "#9ca3af",
    Repair.Difficulty.SIMPLE: "#86efac",
    Repair.Difficulty.NORMAL: "#7dd3fc",
    Repair.Difficulty.DIFFICULT: "#fb923c",
    Repair.Difficulty.VERY_DIFFICULT: "#ef4444",
}


class CreatedAtRangeFilter(SimpleListFilter):
    title = _("created at")
    parameter_name = "created_period"

    def lookups(self, request, model_admin):
        return (
            ("7", _("Last 7 days")),
            ("30", _("Last 30 days")),
            ("365", _("Last year")),
        )

    def queryset(self, request, queryset):
        if self.value():
            days = int(self.value())
            return queryset.filter(created_at__gte=timezone.now().date() - timedelta(days=days))
        return queryset


class RepairPartUsageInline(admin.TabularInline):
    model = RepairPartUsage
    extra = 1


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "colored_status",
        "device",
        "serial_number",
        "colored_difficulty",
        "created_by",
        "total_parts_cost",
    )
    list_filter = ("status", "device", CreatedAtRangeFilter, "repair_difficulty")
    search_fields = ("serial_number", "defect", "note")
    inlines = [RepairPartUsageInline]
    readonly_fields = ("created_at", "total_parts_cost")
    actions = ("mark_as_completed", "write_off_parts_action", "release_reserved_parts_action")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "created_at",
                    "device",
                    "created_by",
                    "serial_number",
                    "defect",
                    "repair_difficulty",
                    "status",
                    "type_of_repair",
                    "note",
                    "total_parts_cost",
                )
            },
        ),
    )

    @admin.display(description=_("Status"))
    def colored_status(self, obj: Repair):
        color = STATUS_COLORS[obj.status]
        return format_html('<span style="background:{};color:white;padding:2px 8px;border-radius:6px;">{}</span>', color, obj.status)

    @admin.display(description=_("Difficulty"))
    def colored_difficulty(self, obj: Repair):
        color = DIFFICULTY_COLORS[obj.repair_difficulty]
        return format_html(
            '<span style="background:{};color:#111;padding:2px 8px;border-radius:6px;">{}</span>',
            color,
            obj.repair_difficulty,
        )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name="Admin").exists():
            return qs
        if request.user.groups.filter(name="Technician").exists():
            return qs.filter(created_by=request.user)
        return qs.none()

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name="Technician").exists() and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and request.user.groups.filter(name="Technician").exists() and obj.created_by != request.user:
            return False
        return super().has_change_permission(request, obj)

    @admin.action(description=_("Mark selected repairs as completed"))
    def mark_as_completed(self, request, queryset):
        for repair in queryset:
            repair.status = Repair.Status.COMPLETED
            repair.full_clean()
            repair.save(update_fields=["status"])
        self.message_user(request, _("Selected repairs were marked as completed."), level=messages.SUCCESS)

    @admin.action(description=_("Write-off parts for selected repairs"))
    def write_off_parts_action(self, request, queryset):
        for repair in queryset:
            repair.write_off_parts()
        self.message_user(request, _("Parts were written off."), level=messages.SUCCESS)

    @admin.action(description=_("Release reserved parts"))
    def release_reserved_parts_action(self, request, queryset):
        for repair in queryset:
            repair.release_reserved_parts()
        self.message_user(request, _("Reserved parts released."), level=messages.SUCCESS)

    def changelist_view(self, request, extra_context=None):
        now = timezone.now()
        qs = self.get_queryset(request)
        extra_context = extra_context or {}
        extra_context["stats_week"] = (
            qs.filter(status=Repair.Status.COMPLETED)
            .annotate(period=TruncWeek("created_at"))
            .values("period")
            .annotate(total=Count("id"))
            .order_by("-period")[:8]
        )
        extra_context["stats_month"] = (
            qs.filter(status=Repair.Status.COMPLETED)
            .annotate(period=TruncMonth("created_at"))
            .values("period")
            .annotate(total=Count("id"))
            .order_by("-period")[:12]
        )
        extra_context["stats_year"] = (
            qs.filter(status=Repair.Status.COMPLETED)
            .annotate(period=TruncYear("created_at"))
            .values("period")
            .annotate(total=Count("id"))
            .order_by("-period")[:5]
        )
        extra_context["top_devices"] = qs.values("device__name").annotate(total=Count("id")).order_by("-total")[:5]
        extra_context["top_defects"] = qs.values("defect").annotate(total=Count("id")).order_by("-total")[:5]
        extra_context["difficulty_stats"] = qs.values("repair_difficulty").annotate(total=Count("id")).order_by("-total")
        extra_context["current_date"] = now
        return super().changelist_view(request, extra_context=extra_context)
