from django.contrib import admin
from django.utils.html import format_html

from sos.models import SOSAlert


@admin.register(SOSAlert)
class SOSAlertAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status_badge",
        "district_name",
        "coordinates_display",
        "distance_to_district_km",
        "source_id",
        "received_at",
        "sent_at",
    )
    list_filter = ("status", "is_inside_boundary", "assigned_district", "received_at")
    search_fields = (
        "source_id",
        "source_telegram_username",
        "source_telegram_first_name",
        "device_info",
        "notes",
    )
    readonly_fields = (
        "received_at",
        "processed_at",
        "sent_at",
        "raw_payload",
        "google_maps_link",
        "telegram_info",
    )
    autocomplete_fields = ("assigned_district",)
    date_hierarchy = "received_at"
    ordering = ("-received_at",)

    fieldsets = (
        (
            "SOS ma'lumotlari",
            {
                "fields": (
                    "status",
                    "latitude",
                    "longitude",
                    "google_maps_link",
                    "source_id",
                    "device_info",
                    "notes",
                )
            },
        ),
        (
            "Tashqi Telegram bot (manba)",
            {
                "fields": (
                    "source_telegram_user_id",
                    "source_telegram_username",
                    "source_telegram_first_name",
                    "source_telegram_message_id",
                    "source_telegram_chat_id",
                ),
                "description": "Foydalanuvchi tashqi botga location yuborgan paytdagi ma'lumotlar",
            },
        ),
        (
            "Tuman yo'naltirish",
            {
                "fields": (
                    "assigned_district",
                    "distance_to_district_km",
                    "match_method",
                    "is_inside_boundary",
                )
            },
        ),
        (
            "Telegram (bizning bot → tuman guruhi)",
            {"fields": ("telegram_info", "telegram_chat_id", "telegram_message_id", "error_message")},
        ),
        ("Tashqi payload", {"fields": ("raw_payload",), "classes": ("collapse",)}),
        (
            "Vaqt",
            {"fields": ("received_at", "processed_at", "sent_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Holat")
    def status_badge(self, obj):
        colors = {
            SOSAlert.Status.RECEIVED: "secondary",
            SOSAlert.Status.ROUTED: "info",
            SOSAlert.Status.SENT: "success",
            SOSAlert.Status.FAILED: "danger",
            SOSAlert.Status.NO_DISTRICT: "warning",
            SOSAlert.Status.NO_GROUP: "warning",
        }
        icons = {
            SOSAlert.Status.RECEIVED: "📥",
            SOSAlert.Status.ROUTED: "🔀",
            SOSAlert.Status.SENT: "✅",
            SOSAlert.Status.FAILED: "❌",
            SOSAlert.Status.NO_DISTRICT: "⚠️",
            SOSAlert.Status.NO_GROUP: "⚠️",
        }
        color = colors.get(obj.status, "secondary")
        icon = icons.get(obj.status, "")
        return format_html(
            '<span class="badge badge-{}">{} {}</span>',
            color,
            icon,
            obj.get_status_display(),
        )

    @admin.display(description="Tuman")
    def district_name(self, obj):
        if obj.assigned_district:
            return obj.assigned_district.name
        return "—"

    @admin.display(description="Koordinatalar")
    def coordinates_display(self, obj):
        return format_html("📍 {}, {}", obj.latitude, obj.longitude)

    @admin.display(description="Xarita")
    def google_maps_link(self, obj):
        if not obj.pk:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" class="btn btn-sm btn-info">🗺 Google Maps</a>',
            obj.google_maps_url,
        )

    @admin.display(description="Telegram holati")
    def telegram_info(self, obj):
        if obj.telegram_chat_id:
            return format_html(
                "Chat: <code>{}</code> | Msg: <code>{}</code>",
                obj.telegram_chat_id,
                obj.telegram_message_id or "—",
            )
        return "Yuborilmagan"
