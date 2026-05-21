from django.urls import path

from dashboard.views import HomeView, api_docs

app_name = "dashboard"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/docs/", api_docs, name="api-docs"),
]
