import hashlib
import logging
from contextlib import contextmanager

import redis
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string

from apps.users.models import User, UserRole

from .models import Platform, SocialAccount, SocialAccountKind

logger = logging.getLogger(__name__)


def get_notification_account() -> SocialAccount:
    account = SocialAccount.objects.filter(
        platform=Platform.TELEGRAM,
        kind=SocialAccountKind.NOTIFICATIONS,
        is_active=True,
    ).first()
    if not account:
        raise ImproperlyConfigured('Нет активного Telegram-аккаунта уведомлений (kind=notifications)')
    return account


def get_system_actor() -> User:
    user, _ = User.objects.get_or_create(
        email='system@inkhaip.local',
        defaults={
            'role': UserRole.AI_AGENT,
            'is_active': True,
            'is_staff': False,
            'password': make_password(get_random_string(32)),
        },
    )
    return user


def build_social_post_idempotency_key(draft_post_id, social_account_id, platform, scheduled_at) -> str:
    raw = f'{draft_post_id}:{social_account_id}:{platform}:{scheduled_at.isoformat()}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _get_redis_client():
    redis_url = getattr(settings, 'REDIS_URL', None) or settings.CELERY_BROKER_URL
    return redis.Redis.from_url(redis_url)


@contextmanager
def social_post_lock(post_id, timeout_seconds=120):
    try:
        lock = _get_redis_client().lock(f'lock:socialpost:{post_id}', timeout=timeout_seconds, blocking=False)
        acquired = lock.acquire(blocking=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning('social_publish_lock_fallback', extra={'post_id': str(post_id), 'error': str(exc)})
        yield True
        return

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock.release()
            except Exception:  # noqa: BLE001
                pass


def check_redis_health() -> bool:
    try:
        client = _get_redis_client()
        return bool(client.ping())
    except Exception:  # noqa: BLE001
        return False
