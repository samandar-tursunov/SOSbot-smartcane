from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from districts.models import District
from sos.models import SOSAlert


class HomeView(TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        alerts = SOSAlert.objects.select_related("assigned_district").order_by("-received_at")

        ctx.update(
            {
                "total_alerts": alerts.count(),
                "sent_alerts": alerts.filter(status=SOSAlert.Status.SENT).count(),
                "failed_alerts": alerts.filter(
                    status__in=[
                        SOSAlert.Status.FAILED,
                        SOSAlert.Status.NO_DISTRICT,
                        SOSAlert.Status.NO_GROUP,
                    ]
                ).count(),
                "active_districts": District.objects.filter(is_active=True).count(),
                "recent_alerts": alerts[:10],
                "districts": District.objects.filter(is_active=True).annotate(
                    alert_count=Count("sos_alerts"),
                    group_count=Count("telegram_groups", filter=Q(telegram_groups__is_active=True)),
                ),
            }
        )
        return ctx


def api_docs(request):
    return render(
        request,
        "dashboard/api_docs.html",
        {
            "endpoint": request.build_absolute_uri(reverse("sos:sos-location")),
            "health_endpoint": request.build_absolute_uri(reverse("sos:health")),
        },
    )
