from django.urls import path

from sos.views import SOSHealthView, SOSLocationView

app_name = "sos"

urlpatterns = [
    path("v1/sos/location/", SOSLocationView.as_view(), name="sos-location"),
    path("v1/health/", SOSHealthView.as_view(), name="health"),
]
