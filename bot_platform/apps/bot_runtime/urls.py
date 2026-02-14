from django.urls import path

from apps.bot_runtime.views import telegram_webhook

urlpatterns = [
    path("webhook/<slug:slug>/", telegram_webhook, name="telegram-webhook"),
]
