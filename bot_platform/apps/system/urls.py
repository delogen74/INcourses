from django.urls import path

from apps.system.views import healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
]
