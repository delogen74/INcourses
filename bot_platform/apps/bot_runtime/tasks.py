from celery import shared_task

from apps.bot_runtime.manager import BotManager
from apps.bots.models import Bot


@shared_task(bind=True, soft_time_limit=10, time_limit=20)
def process_telegram_update(self, bot_id: str, update: dict) -> None:
    try:
        bot = Bot.objects.get(id=bot_id)
    except Bot.DoesNotExist:
        return
    BotManager.dispatch_update(bot, update)


@shared_task(bind=True, soft_time_limit=10, time_limit=20)
def heavy_job(self, bot_id: str, metadata: dict | None = None) -> dict | None:
    try:
        bot = Bot.objects.get(id=bot_id)
    except Bot.DoesNotExist:
        return None
    return {"bot": bot.slug, "status": "done", "metadata": metadata or {}}
