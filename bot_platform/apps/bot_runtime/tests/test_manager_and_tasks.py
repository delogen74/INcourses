import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from apps.bot_runtime.manager import BotManager
from apps.bot_runtime.tasks import heavy_job, process_telegram_update
from apps.bots.models import Bot
from apps.logs.models import BotLog


class BotRuntimeTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        bot_dir = Path(self.temp_dir.name)
        (bot_dir / "bot.py").write_text(
            "class BotHandler:\n"
            "    def __init__(self, bot):\n"
            "        self.bot = bot\n"
            "    def handle_update(self, update):\n"
            "        return update\n"
        )
        self.bot = Bot(name="Runtime Bot", slug="runtime-bot", code_path=str(bot_dir))
        self.bot.set_token("456:DEF")
        self.bot.save()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_routing_writes_log_and_metrics(self):
        BotManager.dispatch_update(self.bot, {"update_id": 1})
        self.bot.refresh_from_db()
        self.assertTrue(BotLog.objects.filter(bot=self.bot, level=BotLog.LEVEL_INFO).exists())
        self.assertEqual(self.bot.updates_count, 1)

    def test_dispatch_error_restarts_and_increments_errors(self):
        bot_dir = Path(self.temp_dir.name)
        (bot_dir / "bot.py").write_text(
            "class BotHandler:\n"
            "    def __init__(self, bot):\n"
            "        self.bot = bot\n"
            "    def handle_update(self, update):\n"
            "        raise RuntimeError('boom')\n"
        )
        BotManager._instances.pop(self.bot.slug, None)
        BotManager.dispatch_update(self.bot, {"update_id": 2})
        self.bot.refresh_from_db()
        self.assertEqual(self.bot.errors_count, 1)
        self.assertTrue(BotLog.objects.filter(bot=self.bot, level=BotLog.LEVEL_ERROR).exists())

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_celery_tasks(self):
        process_telegram_update(str(self.bot.id), {"update_id": 10})
        result = heavy_job(str(self.bot.id), {"kind": "sync"})
        self.assertEqual(result["status"], "done")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_celery_tasks_ignore_deleted_bot(self):
        bot_id = str(self.bot.id)
        self.bot.delete()
        self.assertIsNone(process_telegram_update(bot_id, {"update_id": 11}))
        self.assertIsNone(heavy_job(bot_id, {"kind": "sync"}))
