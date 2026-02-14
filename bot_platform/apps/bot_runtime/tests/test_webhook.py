import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.bots.models import Bot


@override_settings(TELEGRAM_WEBHOOK_SECRET="global-secret")
class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.bot = Bot(name="Test Bot", slug="test-bot", webhook_secret="bot-secret")
        self.bot.set_token("123:ABC")
        self.bot.save()

    @patch("apps.bot_runtime.views.process_telegram_update.delay")
    def test_webhook_accepts_valid_payload(self, delay_mock):
        response = self.client.post(
            reverse("telegram-webhook", kwargs={"slug": "test-bot"}),
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="bot-secret",
        )
        self.assertEqual(response.status_code, 200)
        delay_mock.assert_called_once()

    def test_webhook_rejects_bad_secret(self):
        response = self.client.post(
            reverse("telegram-webhook", kwargs={"slug": "test-bot"}),
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong",
        )
        self.assertEqual(response.status_code, 403)

    @patch("apps.bot_runtime.views.process_telegram_update.delay")
    def test_webhook_fallbacks_to_global_secret(self, delay_mock):
        self.bot.webhook_secret = ""
        self.bot.save(update_fields=["webhook_secret"])
        response = self.client.post(
            reverse("telegram-webhook", kwargs={"slug": "test-bot"}),
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="global-secret",
        )
        self.assertEqual(response.status_code, 200)
        delay_mock.assert_called_once()

    def test_webhook_rejects_inactive_bot(self):
        self.bot.is_active = False
        self.bot.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("telegram-webhook", kwargs={"slug": "test-bot"}),
            data=json.dumps({"update_id": 1}),
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="bot-secret",
        )
        self.assertEqual(response.status_code, 403)
