from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import redis


@require_GET
def healthcheck(request):
    db_ok = True
    redis_ok = True

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        db_ok = False

    try:
        redis.from_url(settings.CELERY_BROKER_URL).ping()
    except Exception:
        redis_ok = False

    status = 200 if db_ok and redis_ok else 503
    return JsonResponse({"status": "ok" if status == 200 else "degraded", "db": db_ok, "redis": redis_ok}, status=status)
