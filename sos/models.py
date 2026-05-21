from django.db import models


class SOSAlert(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Qabul qilindi"
        ROUTED = "routed", "Tumanga yo'naltirildi"
        SENT = "sent", "Telegramga yuborildi"
        FAILED = "failed", "Xato"
        NO_DISTRICT = "no_district", "Tuman topilmadi"
        NO_GROUP = "no_group", "Guruh topilmadi"

    source_id = models.CharField(
        "Tashqi manba ID",
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Tashqi Telegram bot xabari noyob identifikatori",
    )
    latitude = models.DecimalField("Kenglik", max_digits=10, decimal_places=7)
    longitude = models.DecimalField("Uzunlik", max_digits=10, decimal_places=7)

    # Tashqi Telegram botdan kelgan foydalanuvchi ma'lumotlari
    source_telegram_user_id = models.BigIntegerField(
        "Tashqi bot — user ID",
        null=True,
        blank=True,
        help_text="Location yuborgan foydalanuvchi Telegram ID",
    )
    source_telegram_username = models.CharField(
        "Tashqi bot — username",
        max_length=128,
        blank=True,
    )
    source_telegram_first_name = models.CharField(
        "Tashqi bot — ism",
        max_length=128,
        blank=True,
    )
    source_telegram_message_id = models.BigIntegerField(
        "Tashqi bot — xabar ID",
        null=True,
        blank=True,
    )
    source_telegram_chat_id = models.BigIntegerField(
        "Tashqi bot — chat ID",
        null=True,
        blank=True,
        help_text="Foydalanuvchi location yuborgan chat",
    )

    device_info = models.CharField("Qurilma", max_length=255, blank=True)
    notes = models.TextField("Izoh", blank=True)

    assigned_district = models.ForeignKey(
        "districts.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sos_alerts",
        verbose_name="Tayinlangan tuman",
    )
    distance_to_district_km = models.DecimalField(
        "Tumanga masofa (km)",
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )
    match_method = models.CharField("Aniqlash usuli", max_length=32, blank=True)
    is_inside_boundary = models.BooleanField("Chegara ichida", default=False)

    status = models.CharField(
        "Holat",
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
        db_index=True,
    )
    telegram_chat_id = models.BigIntegerField("Yuborilgan chat ID", null=True, blank=True)
    telegram_message_id = models.BigIntegerField("Telegram xabar ID", null=True, blank=True)
    error_message = models.TextField("Xato xabari", blank=True)

    raw_payload = models.JSONField("Tashqi payload", default=dict, blank=True)
    received_at = models.DateTimeField("Qabul vaqti", auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField("Ishlov vaqti", null=True, blank=True)
    sent_at = models.DateTimeField("Yuborilgan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "SOS xabar"
        verbose_name_plural = "SOS xabarlar"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["-received_at", "status"]),
        ]

    def __str__(self):
        return f"SOS #{self.pk} — {self.latitude}, {self.longitude}"

    @property
    def google_maps_url(self):
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"

    @property
    def yandex_maps_url(self):
        return f"https://yandex.com/maps/?pt={self.longitude},{self.latitude}&z=17"
