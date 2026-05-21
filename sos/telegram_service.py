"""Telegram Bot API orqali xabar yuborish."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


@dataclass
class TelegramSendResult:
    ok: bool
    message_id: int | None = None
    error: str = ""


class TelegramService:
    def __init__(self, token: str | None = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN is not configured")

    @property
    def _base_url(self) -> str:
        return TELEGRAM_API_BASE.format(token=self.token)

    def send_location(self, chat_id: int, latitude: float, longitude: float) -> TelegramSendResult:
        """SOS joylashuvini Telegram guruhiga location sifatida yuboradi."""
        return self._post(
            "sendLocation",
            {
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
    ) -> TelegramSendResult:
        return self._post(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview,
            },
        )

    def send_sos_alert(
        self,
        chat_id: int,
        latitude: float,
        longitude: float,
        message_text: str,
    ) -> tuple[TelegramSendResult, TelegramSendResult]:
        """Avval matn, keyin location yuboradi."""
        msg_result = self.send_message(chat_id, message_text)
        loc_result = self.send_location(chat_id, latitude, longitude)
        return msg_result, loc_result

    def _post(self, method: str, payload: dict) -> TelegramSendResult:
        if not self.token:
            return TelegramSendResult(ok=False, error="Telegram bot token not configured")

        url = f"{self._base_url}/{method}"
        try:
            response = requests.post(url, json=payload, timeout=15)
            data = response.json()
            if data.get("ok"):
                message_id = data.get("result", {}).get("message_id")
                return TelegramSendResult(ok=True, message_id=message_id)
            error = data.get("description", "Unknown Telegram API error")
            logger.error("Telegram API error [%s]: %s", method, error)
            return TelegramSendResult(ok=False, error=error)
        except requests.RequestException as exc:
            logger.exception("Telegram request failed")
            return TelegramSendResult(ok=False, error=str(exc))
