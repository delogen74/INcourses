import json

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.bot_runtime.tasks import process_telegram_update
from apps.bots.models import Bot


def _ratelimit_bot_slug(group, request):
    if not request.resolver_match:
        return "unknown-bot"
    return request.resolver_match.kwargs.get("slug", "unknown-bot")


@csrf_exempt
@require_POST
@ratelimit(key="ip", rate="30/m", block=True)
@ratelimit(key=_ratelimit_bot_slug, rate="120/m", block=True)
def telegram_webhook(request: HttpRequest, slug: str) -> HttpResponse:
    try:
        bot = Bot.objects.get(slug=slug)
    except Bot.DoesNotExist:
        return JsonResponse({"detail": "Bot not found"}, status=404)

    if not bot.is_active:
        return JsonResponse({"detail": "Bot inactive"}, status=403)

    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    expected_secret = bot.webhook_secret or settings.TELEGRAM_WEBHOOK_SECRET
    if expected_secret and secret != expected_secret:
        return JsonResponse({"detail": "Invalid webhook secret"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    process_telegram_update.delay(str(bot.id), payload)
    return JsonResponse({"status": "accepted"}, status=200)
