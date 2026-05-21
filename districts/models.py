from django.db import models


class District(models.Model):
    """Tuman — har bir tuman markazi va chegaralari bilan."""

    name = models.CharField("Nomi", max_length=120, unique=True)
    code = models.CharField(
        "Kod",
        max_length=20,
        unique=True,
        help_text="Qisqa identifikator, masalan: yunusobod",
    )
    center_latitude = models.DecimalField(
        "Markaz kenglik (latitude)",
        max_digits=10,
        decimal_places=7,
    )
    center_longitude = models.DecimalField(
        "Markaz uzunlik (longitude)",
        max_digits=10,
        decimal_places=7,
    )
    description = models.TextField("Tavsif", blank=True)
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        verbose_name = "Tuman"
        verbose_name_plural = "Tumanlar"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def center_coords(self):
        return float(self.center_latitude), float(self.center_longitude)

    @property
    def active_telegram_groups(self):
        return self.telegram_groups.filter(is_active=True)

    @property
    def boundary_points_count(self):
        return self.boundary_points.count()


class DistrictBoundary(models.Model):
    """Tuman chegarasi — polygon nuqtalari tartib bilan."""

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="boundary_points",
        verbose_name="Tuman",
    )
    latitude = models.DecimalField("Kenglik", max_digits=10, decimal_places=7)
    longitude = models.DecimalField("Uzunlik", max_digits=10, decimal_places=7)
    order = models.PositiveIntegerField(
        "Tartib",
        default=0,
        help_text="Polygon nuqtalarining ketma-ketligi",
    )

    class Meta:
        verbose_name = "Chegara nuqtasi"
        verbose_name_plural = "Chegara nuqtalari"
        ordering = ["district", "order"]
        unique_together = [["district", "order"]]

    def __str__(self):
        return f"{self.district.name} — nuqta #{self.order}"


class TelegramGroup(models.Model):
    """Har bir tumanga biriktirilgan Telegram guruh."""

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="telegram_groups",
        verbose_name="Tuman",
    )
    chat_id = models.BigIntegerField(
        "Chat ID",
        help_text="Telegram guruh chat_id (manfiy son bo'lishi mumkin)",
    )
    name = models.CharField("Guruh nomi", max_length=200, blank=True)
    is_primary = models.BooleanField(
        "Asosiy guruh",
        default=False,
        help_text="Bir tumanda bitta asosiy guruh bo'lishi kerak",
    )
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Telegram guruh"
        verbose_name_plural = "Telegram guruhlar"
        ordering = ["district", "-is_primary", "name"]
        unique_together = [["district", "chat_id"]]

    def __str__(self):
        label = self.name or str(self.chat_id)
        primary = " ⭐" if self.is_primary else ""
        return f"{self.district.name} — {label}{primary}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            TelegramGroup.objects.filter(
                district=self.district, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
