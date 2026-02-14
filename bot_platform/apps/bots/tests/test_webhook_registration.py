from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.bots.models import Bot


@override_settings(TELEGRAM_WEBHOOK_BASE_URL="https://bot.example.com")
class BotWebhookRegistrationTests(TestCase):
    @patch("apps.bots.models.requests.post")
    def test_register_webhook(self, post_mock):
        response = MagicMock()
        response.json.return_value = {"ok": True, "result": True}
        response.raise_for_status.return_value = None
        post_mock.return_value = response

        bot = Bot(name="Webhook Bot", slug="webhook-bot")
        bot.set_token("111:ABC")
        bot.save()

        payload = bot.register_webhook()

        self.assertTrue(payload["ok"])
        post_mock.assert_called_once()
        called_url = post_mock.call_args.kwargs["json"]["url"]
        self.assertEqual(called_url, "https://bot.example.com/telegram/webhook/webhook-bot/")
