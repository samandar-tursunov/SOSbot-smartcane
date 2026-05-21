"""Telegram xabar matnlarini chiroyli HTML formatda yaratish."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from districts.models import District
    from sos.models import SOSAlert


def format_sos_message(alert: SOSAlert, district: District) -> str:
    """Telegram guruhiga yuboriladigan SOS xabari."""
    center_lat, center_lon = district.center_coords
    received = alert.received_at.strftime("%d.%m.%Y %H:%M:%S")

    boundary_icon = "✅" if alert.is_inside_boundary else "📌"
    boundary_text = (
        "Tuman chegarasi ichida"
        if alert.is_inside_boundary
        else "Eng yaqin tuman markazi bo'yicha"
    )

    distance = alert.distance_to_district_km
    distance_line = f"📏 <b>Masofa:</b> {distance} km\n" if distance is not None else ""

    source_line = ""
    if alert.source_id:
        source_line = f"🔖 <b>Manba ID:</b> <code>{alert.source_id}</code>\n"

    sender_line = ""
    if alert.source_telegram_user_id or alert.source_telegram_username or alert.source_telegram_first_name:
        name = alert.source_telegram_first_name or "Noma'lum"
        username = f" (@{alert.source_telegram_username})" if alert.source_telegram_username else ""
        user_id = f" — ID: <code>{alert.source_telegram_user_id}</code>" if alert.source_telegram_user_id else ""
        sender_line = f"👤 <b>SOS yuboruvchi:</b> {name}{username}{user_id}\n"
        sender_line += "🤖 <i>Tashqi Telegram bot orqali qabul qilindi</i>\n"

    device_line = ""
    if alert.device_info:
        device_line = f"📱 <b>Qurilma:</b> {alert.device_info}\n"

    notes_line = ""
    if alert.notes:
        notes_line = f"📝 <b>Izoh:</b> {alert.notes}\n"

    return (
        "🆘 <b>SOS SIGNAL — YORDAM KERAK!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏛 <b>Tuman:</b> {district.name}\n"
        f"{boundary_icon} <b>Aniqlash:</b> {boundary_text}\n"
        f"{distance_line}"
        f"{source_line}"
        f"{sender_line}"
        f"{device_line}"
        f"{notes_line}\n"
        "📍 <b>SOS joylashuvi:</b>\n"
        f"   • Kenglik: <code>{alert.latitude}</code>\n"
        f"   • Uzunlik: <code>{alert.longitude}</code>\n\n"
        "🏥 <b>Yordam markazi (tuman markazi):</b>\n"
        f"   • Kenglik: <code>{center_lat}</code>\n"
        f"   • Uzunlik: <code>{center_lon}</code>\n\n"
        "🗺 <b>Xaritada ochish:</b>\n"
        f'   • <a href="{alert.google_maps_url}">Google Maps</a>\n'
        f'   • <a href="{alert.yandex_maps_url}">Yandex Maps</a>\n\n'
        f"🕐 <b>Vaqt:</b> {received}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Tez yordam ko'rsating!"
    )


def format_api_success_response(alert: SOSAlert) -> dict:
    return {
        "success": True,
        "alert_id": alert.pk,
        "status": alert.status,
        "district": {
            "id": alert.assigned_district_id,
            "name": alert.assigned_district.name if alert.assigned_district else None,
            "code": alert.assigned_district.code if alert.assigned_district else None,
        },
        "distance_km": float(alert.distance_to_district_km)
        if alert.distance_to_district_km is not None
        else None,
        "is_inside_boundary": alert.is_inside_boundary,
        "telegram_sent": alert.status == alert.Status.SENT,
        "received_at": alert.received_at.isoformat(),
    }
