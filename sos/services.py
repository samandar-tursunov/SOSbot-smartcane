"""SOS signalini qabul qilish, tumanga yo'naltirish va Telegramga yuborish."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from districts.services import find_district_for_location
from sos.messages import format_sos_message
from sos.models import SOSAlert
from sos.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class SOSProcessingError(Exception):
    def __init__(self, message: str, status: str = SOSAlert.Status.FAILED):
        self.message = message
        self.status = status
        super().__init__(message)


def process_sos_alert(
    latitude: float,
    longitude: float,
    *,
    source_id: str = "",
    device_info: str = "",
    notes: str = "",
    source_telegram_user_id: int | None = None,
    source_telegram_username: str = "",
    source_telegram_first_name: str = "",
    source_telegram_message_id: int | None = None,
    source_telegram_chat_id: int | None = None,
    raw_payload: dict | None = None,
) -> SOSAlert:
    """
    Tashqi Telegram botdan push qilingan locationni ishlov beradi:
    1. Bazaga saqlaydi
    2. Eng mos tumanni topadi
    3. Bizning bot orqali tuman Telegram guruhiga yuboradi
    """
    raw_payload = raw_payload or {}

    with transaction.atomic():
        alert = SOSAlert.objects.create(
            latitude=latitude,
            longitude=longitude,
            source_id=source_id,
            source_telegram_user_id=source_telegram_user_id,
            source_telegram_username=source_telegram_username,
            source_telegram_first_name=source_telegram_first_name,
            source_telegram_message_id=source_telegram_message_id,
            source_telegram_chat_id=source_telegram_chat_id,
            device_info=device_info,
            notes=notes,
            raw_payload=raw_payload,
            status=SOSAlert.Status.RECEIVED,
        )

        match = find_district_for_location(latitude, longitude)
        if not match:
            alert.status = SOSAlert.Status.NO_DISTRICT
            alert.error_message = "Faol tuman topilmadi"
            alert.processed_at = timezone.now()
            alert.save(update_fields=["status", "error_message", "processed_at"])
            logger.warning("No active district found for SOS #%s", alert.pk)
            return alert

        district = match.district
        alert.assigned_district = district
        alert.distance_to_district_km = match.distance_km
        alert.match_method = match.match_method
        alert.is_inside_boundary = match.is_inside_boundary
        alert.status = SOSAlert.Status.ROUTED
        alert.processed_at = timezone.now()
        alert.save(
            update_fields=[
                "assigned_district",
                "distance_to_district_km",
                "match_method",
                "is_inside_boundary",
                "status",
                "processed_at",
            ]
        )

        groups = list(district.active_telegram_groups.order_by("-is_primary"))
        if not groups:
            alert.status = SOSAlert.Status.NO_GROUP
            alert.error_message = f"'{district.name}' tumani uchun faol Telegram guruh yo'q"
            alert.save(update_fields=["status", "error_message"])
            logger.warning("No telegram group for district %s", district.code)
            return alert

        target_group = groups[0]
        message_text = format_sos_message(alert, district)
        telegram = TelegramService()

        msg_result, loc_result = telegram.send_sos_alert(
            chat_id=target_group.chat_id,
            latitude=float(alert.latitude),
            longitude=float(alert.longitude),
            message_text=message_text,
        )

        if msg_result.ok:
            alert.status = SOSAlert.Status.SENT
            alert.telegram_chat_id = target_group.chat_id
            alert.telegram_message_id = msg_result.message_id
            alert.sent_at = timezone.now()
            alert.error_message = "" if loc_result.ok else f"Location xato: {loc_result.error}"
            alert.save(
                update_fields=[
                    "status",
                    "telegram_chat_id",
                    "telegram_message_id",
                    "sent_at",
                    "error_message",
                ]
            )
            logger.info(
                "SOS #%s sent to district %s (chat %s)",
                alert.pk,
                district.code,
                target_group.chat_id,
            )
        else:
            alert.status = SOSAlert.Status.FAILED
            alert.error_message = msg_result.error
            alert.save(update_fields=["status", "error_message"])
            logger.error("Failed to send SOS #%s: %s", alert.pk, msg_result.error)

        return alert
