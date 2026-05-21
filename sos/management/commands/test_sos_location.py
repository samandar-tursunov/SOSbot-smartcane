"""
Tashqi bot location yuborganini simulyatsiya qiladi va SOS oqimini test qiladi.

Ishlatish:
  python manage.py test_sos_location
  python manage.py test_sos_location --district yunusobod
  python manage.py test_sos_location --lat 41.311081 --lon 69.240562
  python manage.py test_sos_location --api
  python manage.py test_sos_location --api --url http://localhost:8000
"""

import json
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from districts.models import District
from districts.services import find_district_for_location
from sos.models import SOSAlert
from sos.services import process_sos_alert

# Toshkent markazi — default test nuqta
DEFAULT_LAT = 41.311081
DEFAULT_LON = 69.240562


class Command(BaseCommand):
    help = "Test SOS location yuborish (tashqi bot POST simulyatsiyasi)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lat",
            type=float,
            default=None,
            help=f"Kenglik (default: {DEFAULT_LAT})",
        )
        parser.add_argument(
            "--lon",
            type=float,
            default=None,
            help=f"Uzunlik (default: {DEFAULT_LON})",
        )
        parser.add_argument(
            "--district",
            type=str,
            default=None,
            help="Tuman kodi bo'yicha uning markaziga test yuborish (masalan: yunusobod)",
        )
        parser.add_argument(
            "--api",
            action="store_true",
            help="To'g'ridan-to'g'ri servis o'rniga HTTP API orqali yuborish (tashqi bot kabi)",
        )
        parser.add_argument(
            "--url",
            type=str,
            default=None,
            help="API base URL (default: PUBLIC_BASE_URL yoki http://localhost:8000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Faqat tuman aniqlash, Telegramga yubormaslik",
        )
        parser.add_argument(
            "--list-districts",
            action="store_true",
            help="Mavjud tumanlar ro'yxatini ko'rsatish",
        )

    def handle(self, *args, **options):
        if options["list_districts"]:
            self._list_districts()
            return

        lat, lon, district_label = self._resolve_coordinates(options)

        self.stdout.write(self.style.HTTP_INFO("\n🆘 SOS test location yuborilmoqda...\n"))
        self.stdout.write(f"  📍 Koordinata: {lat}, {lon}")
        if district_label:
            self.stdout.write(f"  🏛 Tuman: {district_label}")

        if options["dry_run"]:
            self._dry_run(lat, lon)
            return

        if options["api"]:
            self._send_via_api(lat, lon, options["url"])
        else:
            self._send_direct(lat, lon)

    def _resolve_coordinates(self, options):
        if options["district"]:
            try:
                district = District.objects.get(code=options["district"], is_active=True)
            except District.DoesNotExist as exc:
                raise CommandError(
                    f"Tuman topilmadi: '{options['district']}'. "
                    "Ro'yxat: python manage.py test_sos_location --list-districts"
                ) from exc
            lat, lon = district.center_coords
            return lat, lon, district.name

        lat = options["lat"] if options["lat"] is not None else DEFAULT_LAT
        lon = options["lon"] if options["lon"] is not None else DEFAULT_LON
        return lat, lon, None

    def _list_districts(self):
        districts = District.objects.filter(is_active=True).order_by("name")
        if not districts.exists():
            self.stdout.write(self.style.WARNING("Faol tuman yo'q. Avval: python manage.py seed_districts"))
            return

        self.stdout.write(self.style.HTTP_INFO("\n🏛 Mavjud tumanlar:\n"))
        for d in districts:
            groups = d.telegram_groups.filter(is_active=True).count()
            points = d.boundary_points.count()
            self.stdout.write(
                f"  • {d.name:<20} kod={d.code:<16} "
                f"markaz=({d.center_latitude}, {d.center_longitude}) "
                f"guruh={groups} chegara={points}ta"
            )
        self.stdout.write("")

    def _dry_run(self, lat, lon):
        match = find_district_for_location(lat, lon)
        if not match:
            self.stdout.write(self.style.ERROR("❌ Hech qanday faol tuman topilmadi"))
            return

        inside = "chegara ichida ✅" if match.is_inside_boundary else "eng yaqin markaz 📌"
        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Topilgan tuman: {match.district.name} ({inside})\n"
            f"   Masofa: {match.distance_km} km\n"
            f"   Usul: {match.match_method}\n"
        ))

    def _send_direct(self, lat, lon):
        """Tashqi bot POST simulyatsiyasi — to'g'ridan-to'g'ri servis."""
        test_id = f"test-{int(time.time())}"
        alert = process_sos_alert(
            latitude=lat,
            longitude=lon,
            source_id=test_id,
            device_info="test_sos_location command",
            notes="🧪 Test SOS signal",
            source_telegram_user_id=999999999,
            source_telegram_username="test_user",
            source_telegram_first_name="Test",
            source_telegram_message_id=int(time.time()),
            source_telegram_chat_id=999999999,
            raw_payload={"test": True, "source": "management_command"},
        )
        self._print_result(alert)

    def _send_via_api(self, lat, lon, url=None):
        """Tashqi bot kabi HTTP POST /api/v1/sos/location/"""
        base = url or settings.PUBLIC_BASE_URL or "http://localhost:8000"
        endpoint = f"{base.rstrip('/')}/api/v1/sos/location/"
        api_key = settings.SOS_API_KEY

        if not api_key:
            raise CommandError("SOS_API_KEY .env da sozlanmagan")

        payload = {
            "location": {"latitude": lat, "longitude": lon},
            "telegram_user_id": 999999999,
            "telegram_username": "test_user",
            "telegram_first_name": "Test",
            "telegram_message_id": int(time.time()),
            "telegram_chat_id": 999999999,
            "notes": "🧪 Test SOS signal (API)",
        }

        self.stdout.write(f"  📡 POST {endpoint}\n")

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise CommandError(f"API ga ulanib bo'lmadi: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise CommandError(f"JSON javob kelmadi (HTTP {response.status_code}): {response.text[:200]}")

        self.stdout.write(f"  HTTP {response.status_code}\n")
        self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

        if response.status_code in (200, 201) and data.get("success"):
            self.stdout.write(self.style.SUCCESS("✅ SOS muvaffaqiyatli yuborildi!"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Xato: {data.get('error', 'noma\'lum')}"))

    def _print_result(self, alert: SOSAlert):
        status_styles = {
            SOSAlert.Status.SENT: self.style.SUCCESS,
            SOSAlert.Status.ROUTED: self.style.WARNING,
            SOSAlert.Status.FAILED: self.style.ERROR,
            SOSAlert.Status.NO_DISTRICT: self.style.ERROR,
            SOSAlert.Status.NO_GROUP: self.style.ERROR,
        }
        style = status_styles.get(alert.status, self.style.WARNING)

        self.stdout.write(style(f"\n{'='*40}"))
        self.stdout.write(style(f"  Alert ID   : #{alert.pk}"))
        self.stdout.write(style(f"  Holat      : {alert.get_status_display()} ({alert.status})"))

        if alert.assigned_district:
            inside = "✅ chegara ichida" if alert.is_inside_boundary else "📌 eng yaqin"
            self.stdout.write(style(f"  Tuman      : {alert.assigned_district.name} ({inside})"))
            self.stdout.write(style(f"  Masofa     : {alert.distance_to_district_km} km"))

        if alert.status == SOSAlert.Status.SENT:
            self.stdout.write(style(f"  Telegram   : chat {alert.telegram_chat_id}, msg {alert.telegram_message_id}"))
            self.stdout.write(self.style.SUCCESS("\n✅ Telegram guruhiga yuborildi!\n"))
        elif alert.error_message:
            self.stdout.write(self.style.ERROR(f"  Xato       : {alert.error_message}\n"))
        else:
            self.stdout.write("")
