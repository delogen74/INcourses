import importlib.util
import logging
import traceback
from pathlib import Path
from typing import Any

from apps.logs.models import BotLog

logger = logging.getLogger(__name__)


class BotManager:
    _instances: dict[str, Any] = {}

    @classmethod
    def load_instance(cls, bot) -> Any:
        if not bot.code_path:
            raise RuntimeError("Bot code path is empty")

        bot_file = Path(bot.code_path) / "bot.py"
        if not bot_file.exists():
            raise RuntimeError("bot.py not found")

        spec = importlib.util.spec_from_file_location(f"{bot.slug}_bot", bot_file)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load bot module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "BotHandler"):
            raise RuntimeError("bot.py must expose BotHandler")

        handler_cls = getattr(module, "BotHandler")
        instance = handler_cls(bot=bot)
        cls._instances[bot.slug] = instance
        return instance

    @classmethod
    def get_instance(cls, bot) -> Any:
        instance = cls._instances.get(bot.slug)
        if instance is None:
            instance = cls.load_instance(bot)
        return instance

    @classmethod
    def restart(cls, bot) -> Any:
        cls._instances.pop(bot.slug, None)
        return cls.load_instance(bot)

    @classmethod
    def dispatch_update(cls, bot, update: dict) -> None:
        if not bot.is_active:
            BotLog.objects.create(
                bot=bot, level=BotLog.LEVEL_WARNING, message="Bot is inactive", payload=update
            )
            return

        instance = cls.get_instance(bot)
        try:
            instance.handle_update(update)
            bot.mark_update_processed(success=True)
            BotLog.objects.create(
                bot=bot, level=BotLog.LEVEL_INFO, message="Update processed", payload=update
            )
        except Exception as exc:
            tb = traceback.format_exc()
            logger.exception("Failed to process update for %s", bot.slug)
            restart_message = ""
            try:
                cls.restart(bot)
                restart_message = " | runtime instance restarted"
            except Exception:
                restart_message = " | runtime restart failed"
                tb = f"{tb}\n\nRestart traceback:\n{traceback.format_exc()}"

            bot.mark_update_processed(success=False)
            BotLog.objects.create(
                bot=bot,
                level=BotLog.LEVEL_ERROR,
                message=f"{exc}{restart_message}",
                payload=update,
                traceback=tb,
            )
