from django.contrib import admin
from django.utils.html import format_html

from districts.models import District, DistrictBoundary, TelegramGroup


class DistrictBoundaryInline(admin.TabularInline):
    model = DistrictBoundary
    extra = 1
    fields = ("order", "latitude", "longitude")
    ordering = ("order",)


class TelegramGroupInline(admin.TabularInline):
    model = TelegramGroup
    extra = 1
    fields = ("name", "chat_id", "is_primary", "is_active")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "center_display",
        "boundary_count",
        "telegram_groups_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at")
    inlines = [DistrictBoundaryInline, TelegramGroupInline]
    fieldsets = (
        (
            "Asosiy ma'lumotlar",
            {"fields": ("name", "code", "description", "is_active")},
        ),
        (
            "Markaz koordinatalari",
            {
                "fields": ("center_latitude", "center_longitude"),
                "description": "Yordam yuboriladigan tuman markazi",
            },
        ),
        ("Vaqt", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Markaz")
    def center_display(self, obj):
        return format_html(
            '<span class="badge badge-info">📍 {}, {}</span>',
            obj.center_latitude,
            obj.center_longitude,
        )

    @admin.display(description="Chegara nuqtalari")
    def boundary_count(self, obj):
        count = obj.boundary_points_count
        color = "success" if count >= 3 else "warning"
        return format_html('<span class="badge badge-{}">{} ta</span>', color, count)

    @admin.display(description="Telegram guruhlar")
    def telegram_groups_count(self, obj):
        count = obj.telegram_groups.filter(is_active=True).count()
        return format_html('<span class="badge badge-primary">{} ta</span>', count)


@admin.register(DistrictBoundary)
class DistrictBoundaryAdmin(admin.ModelAdmin):
    list_display = ("district", "order", "latitude", "longitude")
    list_filter = ("district",)
    search_fields = ("district__name",)
    ordering = ("district", "order")


@admin.register(TelegramGroup)
class TelegramGroupAdmin(admin.ModelAdmin):
    list_display = (
        "district",
        "name",
        "chat_id",
        "primary_badge",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "is_primary", "district")
    search_fields = ("name", "chat_id", "district__name")
    autocomplete_fields = ("district",)

    @admin.display(description="Asosiy")
    def primary_badge(self, obj):
        if obj.is_primary:
            return format_html('<span class="badge badge-warning">⭐ Asosiy</span>')
        return "—"
