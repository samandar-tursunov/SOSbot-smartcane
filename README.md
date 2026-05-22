# 🆘 SOSbot SmartCane

Tashqi **Telegram bot**dan kelgan SOS joylashuvini eng yaqin tumanga yo'naltirib, **bizning Telegram bot** orqali tuman guruhiga xabar yuboradigan Django tizimi.

## Arxitektura

```
Foydalanuvchi
    │
    ▼ location yuboradi
Tashqi Telegram bot (SmartCane bot)
    │
    ▼ POST /api/v1/sos/location/  (latitude + longitude push)
SOSbot Server (Django) — sizning serveringiz
    │
    ├──▶ PostgreSQL (tumanlar, chegaralar, guruhlar, alertlar)
    │
    └──▶ Bizning Telegram bot ──▶ Tuman Telegram guruhi
```

**Muhim:** Bu server tashqi bot emas. Tashqi bot location olganda, o'sha zahoti shu serverga HTTP POST qiladi. Server tumanni aniqlaydi va **alohida** (bizning) bot orqali tuman guruhiga yuboradi.

## Ma'lumotlar bazasi

| Model | Tavsif |
|-------|--------|
| `District` | Tuman nomi, kodi, markaz koordinatalari |
| `DistrictBoundary` | Tuman chegara polygon nuqtalari (tartib bilan) |
| `TelegramGroup` | Tumanga biriktirilgan Telegram `chat_id` |
| `SOSAlert` | Qabul qilingan SOS signallar va ularning holati |

## Tez boshlash (Docker)

```bash
# 1. Muhit o'zgaruvchilarini nusxalash
cp .env.example .env

# 2. .env faylini tahrirlang:
#    - TELEGRAM_BOT_TOKEN
#    - SOS_API_KEY
#    - SECRET_KEY

# 3. Ishga tushirish (makemigrations + migrate avtomatik bajariladi)
docker compose up --build -d

# 4. Tumanlarni yuklash (10 ta Toshkent tumani)
docker compose exec web python manage.py seed_districts
```

Docker `entrypoint.sh` har safar konteyner ishga tushganda avtomatik:
- `makemigrations districts sos`
- `migrate`
- admin foydalanuvchi yaratish (`CREATE_SUPERUSER=true`)

**Manzillar:**
- Dashboard: http://localhost:8000
- Admin panel: http://localhost:8000/admin (admin / admin123)
- API docs: http://localhost:8000/api/docs/
- Health: http://localhost:8000/api/v1/health/

---

## Tashqi Telegram bot integratsiyasi

Tashqi botda foydalanuvchi location yuborgan paytda, bot shu koordinatalarni bizning serverga push qiladi.

### Autentifikatsiya

Har bir so'rovda `X-API-Key` header majburiy:

```http
X-API-Key: your-secure-api-key-for-external-service
```

Alternativ: `Authorization: Bearer <SOS_API_KEY>`

### SOS Location endpoint

```http
POST /api/v1/sos/location/
Content-Type: application/json
X-API-Key: your-secure-api-key-for-external-service
```

**Minimal request** (faqat koordinata yetarli):

```json
{
  "latitude": 41.3110810,
  "longitude": 69.2405620
}
```

**Tavsiya etilgan request** (Telegram ma'lumotlari bilan):

```json
{
  "location": {
    "latitude": 41.3110810,
    "longitude": 69.2405620
  },
  "telegram_user_id": 123456789,
  "telegram_username": "foydalanuvchi",
  "telegram_first_name": "Ali",
  "telegram_message_id": 42,
  "telegram_chat_id": 123456789
}
```

| Maydon | Turi | Majburiy | Tavsif |
|--------|------|----------|--------|
| `latitude` | decimal | ✅* | Kenglik (yoki `location` ichida) |
| `longitude` | decimal | ✅* | Uzunlik (yoki `location` ichida) |
| `location` | object | ✅* | Telegram `location` obyekti |
| `telegram_user_id` | int | ❌ | `message.from.id` |
| `telegram_username` | string | ❌ | `message.from.username` |
| `telegram_first_name` | string | ❌ | `message.from.first_name` |
| `telegram_message_id` | int | ❌ | `message.message_id` |
| `telegram_chat_id` | int | ❌ | `message.chat.id` |
| `source_id` | string | ❌ | Noyob ID (bo'sh bo'lsa avtomatik yaratiladi) |
| `notes` | string | ❌ | Qo'shimcha izoh |

\* `latitude`+`longitude` yoki `location.latitude`+`location.longitude` majburiy.

### Tashqi botda qanday chaqirish (pseudocode)

```python
# Tashqi Telegram bot — foydalanuvchi location yuborganida:
async def on_location(message):
    location = message.location
    await httpx.post(
        "https://SIZNING-SERVER/api/v1/sos/location/",
        headers={"X-API-Key": SOS_API_KEY},
        json={
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude,
            },
            "telegram_user_id": message.from_user.id,
            "telegram_username": message.from_user.username or "",
            "telegram_first_name": message.from_user.first_name or "",
            "telegram_message_id": message.message_id,
            "telegram_chat_id": message.chat.id,
        },
    )
```

**Muvaffaqiyatli javob (201):**

```json
{
  "success": true,
  "alert_id": 42,
  "status": "sent",
  "district": {
    "id": 3,
    "name": "Yunusobod",
    "code": "yunusobod"
  },
  "distance_km": 1.245,
  "is_inside_boundary": true,
  "telegram_sent": true,
  "received_at": "2026-05-22T14:30:01+05:00"
}
```

**Xato kodlari:**

| HTTP | Sabab |
|------|-------|
| 401 | API kalit noto'g'ri yoki yo'q |
| 400 | Validatsiya xatosi |
| 422 | Tuman/guruh topilmadi yoki Telegram xatosi |

### cURL misoli

```bash
curl -X POST "http://localhost:8000/api/v1/sos/location/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key-for-external-service" \
  -d '{
    "latitude": 41.3110810,
    "longitude": 69.2405620,
    "source_id": "test-001",
    "device_info": "SmartCane Demo"
  }'
```

### Health check

```bash
curl http://localhost:8000/api/v1/health/
```

---

## Ishlash tartibi

1. Foydalanuvchi **tashqi Telegram bot**ga location yuboradi
2. Tashqi bot o'sha locationni **sizning serveringizga** HTTP POST qiladi
3. Server nuqtani tuman chegaralari bilan solishtiradi
4. Eng mos tuman tanlanadi
5. **Bizning bot** tumanga biriktirilgan guruhga matn + location yuboradi
6. Natija bazaga saqlanadi

### Telegram xabar formati (namuna)

```
🆘 SOS SIGNAL — YORDAM KERAK!
━━━━━━━━━━━━━━━━━━━━

🏛 Tuman: Yunusobod
✅ Aniqlash: Tuman chegarasi ichida
📏 Masofa: 1.245 km
🔖 Manba ID: device-abc-12345

📍 SOS joylashuvi:
   • Kenglik: 41.3110810
   • Uzunlik: 69.2405620

🏥 Yordam markazi (tuman markazi):
   • Kenglik: 41.3678000
   • Uzunlik: 69.2890000

🗺 Xaritada ochish:
   • Google Maps | Yandex Maps

🕐 Vaqt: 22.05.2026 14:30:01
━━━━━━━━━━━━━━━━━━━━
⚡ Tez yordam ko'rsating!
```

---

## Admin panel sozlash

1. **Tumanlar** — nom, kod, markaz koordinatalari
2. **Chegara nuqtalari** — har tuman uchun polygon (kamida 3 nuqta)
3. **Telegram guruhlar** — `chat_id` va asosiy guruh belgilash

Telegram `chat_id` olish:
1. Botni guruhga qo'shing
2. Guruhda xabar yuboring
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` dan `chat.id` ni oling

---

## Lokal ishlab chiqish (Docker siz)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# POSTGRES_HOST=localhost qiling

python manage.py migrate
python manage.py seed_districts
python manage.py createsuperuser
python manage.py runserver
```

---

## Loyiha tuzilmasi

```
├── config/              # Django sozlamalari, Jazzmin
├── districts/           # Tuman, chegara, Telegram guruh modellari
├── sos/                 # SOS API, Telegram xizmati, alertlar
├── dashboard/           # Frontend dashboard va API docs
├── templates/           # HTML shablonlar
├── static/              # CSS (SOS qizil tema)
├── docker/              # Entrypoint skript
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Muhit o'zgaruvchilari

| O'zgaruvchi | Tavsif |
|-------------|--------|
| `SECRET_KEY` | Django maxfiy kalit |
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni |
| `SOS_API_KEY` | Tashqi servis API kaliti |
| `POSTGRES_*` | PostgreSQL ulanish |
| `PUBLIC_BASE_URL` | Tashqi URL (ixtiyoriy) |

---

## Texnologiyalar

- Django 5.1 + Django REST Framework
- django-jazzmin (admin panel)
- PostgreSQL 16
- Shapely (polygon aniqlash)
- Docker + Gunicorn

## Author 
Samandar Tursunov