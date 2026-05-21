from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("api/", include("sos.urls")),
]

admin.site.site_header = "SOSbot SmartCane Admin"
admin.site.site_title = "SOSbot Admin"
admin.site.index_title = "Boshqaruv paneli"
