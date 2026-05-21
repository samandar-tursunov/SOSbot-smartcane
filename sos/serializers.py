from rest_framework import serializers


class TelegramLocationSerializer(serializers.Serializer):
    """Telegram Bot API `location` obyekti formati."""

    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    horizontal_accuracy = serializers.FloatField(required=False, allow_null=True)
    live_period = serializers.IntegerField(required=False, allow_null=True)


class SOSLocationSerializer(serializers.Serializer):
    """
    Tashqi Telegram bot location push qilganda qabul qilinadigan format.

    Minimal (majburiy):
        {"latitude": 41.31, "longitude": 69.24}

    Telegram uslubida (tavsiya etiladi):
        {
          "location": {"latitude": 41.31, "longitude": 69.24},
          "telegram_user_id": 123456789,
          "telegram_username": "user123",
          "telegram_message_id": 42,
          "telegram_chat_id": 123456789
        }
    """

    # To'g'ridan-to'g'ri koordinatalar
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        help_text="SOS kenglik (Telegram location.latitude)",
    )
    longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        help_text="SOS uzunlik (Telegram location.longitude)",
    )

    # Telegram Bot API location obyekti (tashqi bot shu formatda yuborishi mumkin)
    location = TelegramLocationSerializer(required=False)

    source_id = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        help_text="Noyob ID; bo'sh bo'lsa telegram_message_id dan yaratiladi",
    )
    telegram_user_id = serializers.IntegerField(
        required=False,
        help_text="Location yuborgan foydalanuvchi Telegram ID (message.from.id)",
    )
    telegram_username = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        help_text="Foydalanuvchi @username",
    )
    telegram_first_name = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        help_text="Foydalanuvchi ismi (message.from.first_name)",
    )
    telegram_message_id = serializers.IntegerField(
        required=False,
        help_text="Tashqi botdagi xabar ID (message.message_id)",
    )
    telegram_chat_id = serializers.IntegerField(
        required=False,
        help_text="Chat ID (message.chat.id)",
    )
    device_info = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)

    def validate(self, data):
        lat = data.get("latitude")
        lon = data.get("longitude")
        location = data.get("location")

        if location:
            lat = lat or location["latitude"]
            lon = lon or location["longitude"]

        if lat is None or lon is None:
            raise serializers.ValidationError(
                "latitude va longitude majburiy. "
                "To'g'ridan-to'g'ri yuboring yoki Telegram `location` obyektini qo'shing."
            )

        lat_f, lon_f = float(lat), float(lon)
        if not -90 <= lat_f <= 90:
            raise serializers.ValidationError({"latitude": "Latitude -90 dan 90 gacha bo'lishi kerak."})
        if not -180 <= lon_f <= 180:
            raise serializers.ValidationError({"longitude": "Longitude -180 dan 180 gacha bo'lishi kerak."})

        data["latitude"] = lat
        data["longitude"] = lon
        return data

    def build_source_id(self, data: dict) -> str:
        if data.get("source_id"):
            return data["source_id"]
        msg_id = data.get("telegram_message_id")
        chat_id = data.get("telegram_chat_id")
        if msg_id and chat_id:
            return f"tg-{chat_id}-{msg_id}"
        user_id = data.get("telegram_user_id")
        if user_id and msg_id:
            return f"tg-user-{user_id}-{msg_id}"
        return ""
