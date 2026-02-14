from django.contrib import admin

from inventory.models import Part


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "current_stock", "reserved", "available", "min_stock", "is_low_stock")
    search_fields = ("code", "name", "supplier")
    list_filter = ("supplier",)

    @admin.display(description="Available")
    def available(self, obj: Part) -> int:
        return obj.available_stock

    @admin.display(boolean=True, description="Low stock")
    def is_low_stock(self, obj: Part) -> bool:
        return obj.available_stock < obj.min_stock
