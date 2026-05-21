import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from sos.messages import format_api_success_response
from sos.serializers import SOSLocationSerializer
from sos.services import process_sos_alert

logger = logging.getLogger(__name__)


class SOSAPIKeyMixin:
    """Tashqi servis autentifikatsiyasi — X-API-Key header."""

    def _check_api_key(self, request) -> bool:
        expected = settings.SOS_API_KEY
        if not expected:
            logger.warning("SOS_API_KEY is not set — rejecting request")
            return False
        provided = request.headers.get("X-API-Key") or request.headers.get("Authorization", "")
        if provided.startswith("Bearer "):
            provided = provided[7:]
        return provided == expected


class SOSLocationView(SOSAPIKeyMixin, APIView):
    """
    Tashqi Telegram bot location qabul qilganda shu endpointga push qiladi.

    Oqim:
      Foydalanuvchi → Tashqi Telegram bot (location) → POST bu API → Bizning bot → Tuman guruhi

    POST /api/v1/sos/location/
    Header: X-API-Key: <SOS_API_KEY>
    """

    def post(self, request):
        if not self._check_api_key(request):
            return Response(
                {"success": False, "error": "Unauthorized — invalid or missing API key"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = SOSLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        alert = process_sos_alert(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            source_id=serializer.build_source_id(data),
            device_info=data.get("device_info", ""),
            notes=data.get("notes", ""),
            source_telegram_user_id=data.get("telegram_user_id"),
            source_telegram_username=data.get("telegram_username", ""),
            source_telegram_first_name=data.get("telegram_first_name", ""),
            source_telegram_message_id=data.get("telegram_message_id"),
            source_telegram_chat_id=data.get("telegram_chat_id"),
            raw_payload=dict(request.data),
        )

        response_data = format_api_success_response(alert)
        if alert.status in (alert.Status.FAILED, alert.Status.NO_DISTRICT, alert.Status.NO_GROUP):
            response_data["success"] = False
            response_data["error"] = alert.error_message
            http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        else:
            http_status = status.HTTP_201_CREATED

        return Response(response_data, status=http_status)


class SOSHealthView(APIView):
    """Servis holati tekshiruvi."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from districts.models import District

        return Response(
            {
                "status": "ok",
                "service": "SOSbot SmartCane",
                "active_districts": District.objects.filter(is_active=True).count(),
                "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            }
        )
