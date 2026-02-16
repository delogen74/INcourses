import hashlib
import secrets
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    OWNER = 'owner', 'Владелец'
    EDITOR = 'editor', 'Редактор'
    AI_AGENT = 'ai_agent', 'AI-агент'


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.EDITOR)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ServiceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='service_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    scopes = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Сервисный токен'
        verbose_name_plural = 'Сервисные токены'

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @classmethod
    def generate_token(cls) -> tuple[str, str]:
        raw = secrets.token_urlsafe(48)
        return raw, cls.hash_token(raw)
