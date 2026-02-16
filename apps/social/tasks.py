import logging
import uuid

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_event

from .connectors import CONNECTOR_MAP
from .connectors.telegram import TelegramConnector
from .models import SocialPost
from .services import get_notification_account, get_system_actor, social_post_lock

logger = logging.getLogger(__name__)

TRANSIENT_MARKERS = ('timeout', 'timed out', 'temporarily', '429', 'rate limit', 'too many requests', 'connection')


@shared_task(rate_limit='20/m')
def send_telegram_notification(message: str):
    account = None
    try:
        account = get_notification_account()
        connector = TelegramConnector()

        class DummyDraft:
            title = ''
            content = message
            assets = []

        result = connector.publish(account, DummyDraft())
        if not result.success:
            raise RuntimeError(result.error)

        log_event(
            actor=get_system_actor(),
            action='notification.sent',
            entity=account,
            payload={'channel': 'telegram', 'message': message[:500]},
        )
    except Exception as exc:  # noqa: BLE001
        log_event(
            actor=get_system_actor(),
            action='notification.failed',
            entity=account,
            payload={'channel': 'telegram', 'error': str(exc), 'message': message[:500]},
        )


@shared_task(bind=True, max_retries=5)
def publish_scheduled_social_posts(self):
    now = timezone.now()
    claimed_versions = {}
    with transaction.atomic():
        posts = list(
            SocialPost.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=[SocialPost.Status.SCHEDULED, SocialPost.Status.PENDING],
                scheduled_at__lte=now,
            )[:20]
        )
        for post in posts:
            post.status = SocialPost.Status.PUBLISHING
            if not post.publishing_token:
                post.publishing_token = uuid.uuid4()
                post.publishing_started_at = now
            post.publish_version += 1
            post.save(update_fields=['status', 'publishing_token', 'publishing_started_at', 'publish_version', 'updated_at'])
            claimed_versions[post.id] = post.publish_version

    for post in posts:
        with social_post_lock(post.id, timeout_seconds=getattr(settings, 'PUBLISH_LOCK_TTL_SECONDS', 120)) as acquired:
            if not acquired:
                logger.info('social_publish_lock_skipped', extra={'post_id': str(post.id)})
                continue

            post.refresh_from_db(fields=['status', 'external_id', 'updated_at', 'attempts', 'idempotency_key', 'publishing_token', 'publishing_started_at', 'publish_version'])
            claimed_version = claimed_versions.get(post.id)
            if claimed_version is not None and post.publish_version != claimed_version:
                logger.info(
                    'social_publish_version_mismatch',
                    extra={'post_id': str(post.id), 'claimed_version': claimed_version, 'actual_version': post.publish_version},
                )
                post.status = SocialPost.Status.PENDING
                post.error_message = 'Publish version mismatch; rescheduled.'
                post.publishing_token = None
                post.publishing_started_at = None
                post.save(
                    update_fields=[
                        'status',
                        'error_message',
                        'publishing_token',
                        'publishing_started_at',
                        'updated_at',
                    ]
                )
                log_event(
                    actor=get_system_actor(),
                    action='social.publish_rescheduled',
                    entity=post,
                    payload={
                        'reason': 'publish_version_mismatch',
                        'claimed_version': claimed_version,
                        'actual_version': post.publish_version,
                    },
                )
                continue
            if post.status == SocialPost.Status.PUBLISHED and post.external_id:
                logger.info('social_publish_already_published', extra={'post_id': str(post.id), 'idempotency_key': post.idempotency_key})
                continue
            if post.status != SocialPost.Status.PUBLISHING:
                logger.info('social_publish_status_changed', extra={'post_id': str(post.id), 'status': post.status})
                continue
            stale_ttl_minutes = getattr(settings, 'SOCIAL_PUBLISH_STUCK_TTL_MINUTES', 15)
            if post.publishing_token and post.publishing_started_at and post.publishing_started_at < timezone.now() - timezone.timedelta(minutes=stale_ttl_minutes):
                post.status = SocialPost.Status.FAILED
                post.error_message = 'Detected stale in-flight publish marker. Manual review required to avoid duplicate posting.'
                post.attempts += 1
                post.publishing_token = None
                post.publishing_started_at = None
                post.save(update_fields=['status', 'error_message', 'attempts', 'publishing_token', 'publishing_started_at', 'updated_at'])
                log_event(actor=get_system_actor(), action='social.publish_attempt', entity=post, payload={'status': post.status, 'error': post.error_message})
                continue

            try:
                if not post.social_account.is_active:
                    post.status = SocialPost.Status.FAILED
                    post.error_message = 'Социальный аккаунт деактивирован.'
                    post.attempts += 1
                    post.publishing_token = None
                    post.publishing_started_at = None
                    post.save(update_fields=['status', 'error_message', 'attempts', 'publishing_token', 'publishing_started_at', 'updated_at'])
                    log_event(actor=get_system_actor(), action='social.publish_attempt', entity=post, payload={'status': post.status, 'error': post.error_message})
                    continue

                connector_cls = CONNECTOR_MAP[post.platform]
                connector = connector_cls()
                result = connector.publish(post.social_account, post.draft_post, idempotency_key=post.idempotency_key)

                if result.success:
                    post.status = SocialPost.Status.PUBLISHED
                    post.external_id = result.external_id
                    post.published_at = timezone.now()
                    post.error_message = ''
                    post.publishing_token = None
                    post.publishing_started_at = None
                    send_telegram_notification.delay(
                        f'✅ Опубликовано\nПлатформа: {post.platform}\nЗаголовок: {post.draft_post.title or "Без заголовка"}\nВремя: {post.published_at.isoformat()}'
                    )
                    logger.info('social_publish_success', extra={'platform': post.platform, 'post_id': str(post.id), 'idempotency_key': post.idempotency_key})
                    post.save(update_fields=['status', 'external_id', 'published_at', 'error_message', 'publishing_token', 'publishing_started_at', 'updated_at'])
                else:
                    post.attempts += 1
                    error_text = (result.error or '').lower()
                    is_transient = any(marker in error_text for marker in TRANSIENT_MARKERS)
                    if is_transient:
                        post.status = SocialPost.Status.PENDING
                    else:
                        post.status = SocialPost.Status.FAILED
                    post.error_message = result.error
                    post.publishing_token = None
                    post.publishing_started_at = None
                    logger.warning('social_publish_fail', extra={'platform': post.platform, 'post_id': str(post.id), 'error': result.error, 'idempotency_key': post.idempotency_key, 'transient': is_transient})
                    post.save(update_fields=['status', 'error_message', 'attempts', 'publishing_token', 'publishing_started_at', 'updated_at'])

                log_event(actor=get_system_actor(), action='social.publish_attempt', entity=post, payload={'status': post.status, 'error': post.error_message, 'idempotency_key': post.idempotency_key})
            except Exception as exc:  # noqa: BLE001
                post.attempts += 1
                post.error_message = str(exc)
                post.status = SocialPost.Status.PENDING
                post.publishing_token = None
                post.publishing_started_at = None
                post.save(update_fields=['attempts', 'error_message', 'status', 'publishing_token', 'publishing_started_at', 'updated_at'])

                try:
                    raise self.retry(exc=exc, countdown=min(2 ** post.attempts, 300))
                except MaxRetriesExceededError:
                    post.status = SocialPost.Status.FAILED
                    post.publishing_token = None
                    post.publishing_started_at = None
                    post.save(update_fields=['status', 'publishing_token', 'publishing_started_at', 'updated_at'])
                    log_event(actor=get_system_actor(), action='social.publish_attempt', entity=post, payload={'status': post.status, 'error': post.error_message})


@shared_task
def recover_stuck_social_posts():
    ttl_minutes = getattr(settings, 'SOCIAL_PUBLISH_STUCK_TTL_MINUTES', 15)
    max_retries = getattr(settings, 'SOCIAL_PUBLISH_MAX_RETRIES', 5)
    cutoff = timezone.now() - timezone.timedelta(minutes=ttl_minutes)

    stuck_posts = SocialPost.objects.filter(status=SocialPost.Status.PUBLISHING, updated_at__lt=cutoff)
    for post in stuck_posts:
        post.attempts += 1
        if post.publishing_token:
            post.status = SocialPost.Status.FAILED
            post.error_message = 'Recovery detected in-flight marker; publish outcome unknown. Manual review required.'
            action = 'social.recovery_failed'
        elif post.attempts >= max_retries:
            post.status = SocialPost.Status.FAILED
            post.error_message = 'Recovery: exceeded max retries for stuck publishing.'
            action = 'social.recovery_failed'
        else:
            post.status = SocialPost.Status.PENDING
            post.error_message = 'Recovered from stuck publishing.'
            action = 'social.recovered'
        post.publishing_token = None
        post.publishing_started_at = None
        post.save(update_fields=['status', 'error_message', 'attempts', 'publishing_token', 'publishing_started_at', 'updated_at'])
        log_event(actor=get_system_actor(), action=action, entity=post, payload={'attempts': post.attempts, 'updated_at': post.updated_at.isoformat()})

    return stuck_posts.count()
