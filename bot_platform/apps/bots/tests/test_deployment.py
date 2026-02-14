import tempfile
import zipfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.bots.models import Bot, BotDeployment, MAX_ARCHIVE_SIZE_BYTES


class BotDeploymentTests(TestCase):
    @override_settings(MEDIA_ROOT=Path(tempfile.gettempdir()) / "bot-platform-tests-media")
    def test_upload_and_deploy_zip(self):
        bot = Bot(name="Deploy Bot", slug="deploy-bot")
        bot.set_token("789:GHI")
        bot.save()

        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zip_ref:
                zip_ref.writestr("bot.py", "class BotHandler:\n    def __init__(self, bot):\n        pass\n")
            tmp.seek(0)
            uploaded = SimpleUploadedFile("bot.zip", tmp.read(), content_type="application/zip")

        deployment = BotDeployment.objects.create(bot=bot, version=1, file_archive=uploaded)
        path = deployment.deploy()

        bot.refresh_from_db()
        self.assertEqual(bot.code_version, 1)
        self.assertTrue((path / "bot.py").exists())

    @override_settings(MEDIA_ROOT=Path(tempfile.gettempdir()) / "bot-platform-tests-media")
    def test_zip_slip_is_rejected(self):
        bot = Bot(name="Deploy Bot", slug="deploy-bot-2")
        bot.set_token("123:SAFE")
        bot.save()

        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zip_ref:
                zip_ref.writestr("../escape.py", "print('bad')")
                zip_ref.writestr("bot.py", "class BotHandler:\n    pass\n")
            tmp.seek(0)
            uploaded = SimpleUploadedFile("bad.zip", tmp.read(), content_type="application/zip")

        deployment = BotDeployment.objects.create(bot=bot, version=1, file_archive=uploaded)
        with self.assertRaises(ValidationError):
            deployment.deploy()

    @override_settings(MEDIA_ROOT=Path(tempfile.gettempdir()) / "bot-platform-tests-media")
    def test_large_archive_is_rejected(self):
        bot = Bot(name="Deploy Bot", slug="deploy-bot-3")
        bot.set_token("123:LARGE")
        bot.save()

        oversized = SimpleUploadedFile(
            "large.zip",
            b"x" * (MAX_ARCHIVE_SIZE_BYTES + 1),
            content_type="application/zip",
        )
        deployment = BotDeployment.objects.create(bot=bot, version=1, file_archive=oversized)
        with self.assertRaises(ValidationError):
            deployment.deploy()
