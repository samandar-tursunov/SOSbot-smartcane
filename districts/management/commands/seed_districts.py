"""
Toshkent shahar tumanlari uchun namuna ma'lumotlar.
Haqiqiy chegara koordinatalarini admin panel orqali yangilang.

Ishlatish: python manage.py seed_districts
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from districts.models import District, DistrictBoundary

# Toshkent tumanlari — markaz koordinatalari (taxminiy)
TASHKENT_DISTRICTS = [
    {
        "name": "Bektemir",
        "code": "bektemir",
        "center": (41.2098, 69.3342),
        "boundary_offset": 0.04,
    },
    {
        "name": "Chilonzor",
        "code": "chilonzor",
        "center": (41.2856, 69.2034),
        "boundary_offset": 0.035,
    },
    {
        "name": "Yashnobod",
        "code": "yashnobod",
        "center": (41.2867, 69.3123),
        "boundary_offset": 0.035,
    },
    {
        "name": "Mirobod",
        "code": "mirobod",
        "center": (41.2995, 69.2798),
        "boundary_offset": 0.025,
    },
    {
        "name": "Mirzo Ulug'bek",
        "code": "mirzo_ulugbek",
        "center": (41.3389, 69.3344),
        "boundary_offset": 0.04,
    },
    {
        "name": "Sergeli",
        "code": "sergeli",
        "center": (41.2201, 69.2189),
        "boundary_offset": 0.04,
    },
    {
        "name": "Shayxontohur",
        "code": "shayxontohur",
        "center": (41.3267, 69.2489),
        "boundary_offset": 0.025,
    },
    {
        "name": "Olmazor",
        "code": "olmazor",
        "center": (41.3556, 69.2012),
        "boundary_offset": 0.035,
    },
    {
        "name": "Uchtepa",
        "code": "uchtepa",
        "center": (41.3123, 69.1456),
        "boundary_offset": 0.035,
    },
    {
        "name": "Yunusobod",
        "code": "yunusobod",
        "center": (41.3678, 69.2890),
        "boundary_offset": 0.035,
    },
]


def _square_boundary(lat: float, lon: float, offset: float) -> list[tuple[float, float]]:
    """Markaz atrofida kvadrat polygon (demo uchun)."""
    return [
        (lat - offset, lon - offset),
        (lat - offset, lon + offset),
        (lat + offset, lon + offset),
        (lat + offset, lon - offset),
    ]


class Command(BaseCommand):
    help = "10 ta Toshkent tumani uchun namuna ma'lumotlar yaratadi"

    def handle(self, *args, **options):
        created = 0
        for item in TASHKENT_DISTRICTS:
            lat, lon = item["center"]
            district, was_created = District.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "center_latitude": Decimal(str(lat)),
                    "center_longitude": Decimal(str(lon)),
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

            district.boundary_points.all().delete()
            for order, (b_lat, b_lon) in enumerate(
                _square_boundary(lat, lon, item["boundary_offset"])
            ):
                DistrictBoundary.objects.create(
                    district=district,
                    latitude=Decimal(str(round(b_lat, 7))),
                    longitude=Decimal(str(round(b_lon, 7))),
                    order=order,
                )

            self.stdout.write(self.style.SUCCESS(f"  ✓ {district.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ {len(TASHKENT_DISTRICTS)} tuman tayyor ({created} yangi). "
                "Telegram guruhlarni admin panelda qo'shing."
            )
        )
