import json
import uuid

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def _get_fernet():
    return Fernet(settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY)


class Platform(models.TextChoices):
    VK = 'vk', 'VK'
    TELEGRAM = 'telegram', 'Telegram'
    INSTAGRAM = 'instagram', 'Instagram'
    TIKTOK = 'tiktok', 'TikTok'
    YOUTUBE = 'youtube', 'YouTube'


class SocialAccountKind(models.TextChoices):
    DEFAULT = 'default', 'Обычный'
    NOTIFICATIONS = 'notifications', 'Уведомления'


class SocialAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    kind = models.CharField(max_length=20, choices=SocialAccountKind.choices, default=SocialAccountKind.DEFAULT)
    display_name = models.CharField(max_length=255)
    credentials_encrypted = models.BinaryField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Подключение соцсети'
        verbose_name_plural = 'Подключения соцсетей'
        indexes = [models.Index(fields=['platform', 'kind', 'is_active'])]

    @property
    def credentials(self):
        return json.loads(_get_fernet().decrypt(self.credentials_encrypted).decode())

    def set_credentials(self, data: dict):
        self.credentials_encrypted = _get_fernet().encrypt(json.dumps(data).encode())


class SocialPost(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        READY_FOR_APPROVAL = 'ready_for_approval', 'Готов к согласованию'
        APPROVED = 'approved', 'Согласован'
        REJECTED = 'rejected', 'Отклонён'
        NEEDS_REVISION = 'needs_revision', 'Нужна доработка'
        SCHEDULED = 'scheduled', 'Запланирован'
        PUBLISHING = 'publishing', 'Публикуется'
        PUBLISHED = 'published', 'Опубликован'
        FAILED = 'failed', 'Ошибка'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft_post = models.ForeignKey('content.DraftPost', on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=20, choices=Platform.choices)
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE)
    idempotency_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    scheduled_at = models.DateTimeField()
    publishing_token = models.UUIDField(null=True, blank=True)
    publishing_started_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    external_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    review_comment = models.TextField(blank=True)
    attempts = models.PositiveIntegerField(default=0)
    publish_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Очередь публикаций'
        constraints = [
            models.UniqueConstraint(
                fields=['draft_post', 'platform', 'social_account', 'scheduled_at'],
                name='uniq_draft_platform_account_schedule',
            )
        ]

    def can_transition_to(self, new_status: str) -> bool:
        if self.can_review_transition_to(new_status):
            return True
        if self.can_publish_transition_to(new_status):
            return True
        allowed_transitions = {
            self.Status.NEEDS_REVISION: {self.Status.READY_FOR_APPROVAL},
        }
        return new_status in allowed_transitions.get(self.status, set())

    def can_review_transition_to(self, new_status: str) -> bool:
        if self.status != self.Status.READY_FOR_APPROVAL:
            return False
        return new_status in {
            self.Status.APPROVED,
            self.Status.REJECTED,
            self.Status.NEEDS_REVISION,
        }

    def can_publish_transition_to(self, new_status: str) -> bool:
        allowed_transitions = {
            self.Status.APPROVED: {self.Status.SCHEDULED},
            self.Status.SCHEDULED: {self.Status.PUBLISHING},
            self.Status.PUBLISHING: {self.Status.PUBLISHED, self.Status.FAILED},
        }
        return new_status in allowed_transitions.get(self.status, set())
