import base64
import hashlib
import secrets
import shutil
import uuid
import zipfile
from pathlib import Path

import requests
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


deployment_storage = FileSystemStorage(location=settings.MEDIA_ROOT / "deployments")
MAX_ARCHIVE_SIZE_BYTES = 20 * 1024 * 1024


class Bot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    token = models.TextField(help_text="Encrypted telegram token")
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    webhook_secret = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    code_version = models.PositiveIntegerField(default=0)
    code_path = models.CharField(max_length=512, blank=True)
    config = models.JSONField(default=dict, blank=True)
    last_update_at = models.DateTimeField(null=True, blank=True)
    updates_count = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def _cipher() -> Fernet:
        raw_key = settings.BOT_TOKEN_ENCRYPTION_KEY.encode("utf-8")
        if len(raw_key) != 44:
            raw_key = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
        return Fernet(raw_key)

    def set_token(self, raw_token: str) -> None:
        if not raw_token:
            raise ValidationError("Token is required")
        self.token = self._cipher().encrypt(raw_token.encode("utf-8")).decode("utf-8")
        self.token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def get_token(self) -> str:
        return self._cipher().decrypt(self.token.encode("utf-8")).decode("utf-8")

    def ensure_webhook_secret(self) -> None:
        if not self.webhook_secret:
            self.webhook_secret = secrets.token_urlsafe(32)

    def webhook_url(self) -> str:
        base_url = settings.TELEGRAM_WEBHOOK_BASE_URL.rstrip("/")
        if not base_url:
            raise ValidationError("TELEGRAM_WEBHOOK_BASE_URL must be set")
        return f"{base_url}/telegram/webhook/{self.slug}/"

    def register_webhook(self) -> dict:
        self.ensure_webhook_secret()
        if not self.pk:
            self.save()
        response = requests.post(
            f"https://api.telegram.org/bot{self.get_token()}/setWebhook",
            json={"url": self.webhook_url(), "secret_token": self.webhook_secret},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise ValidationError(payload.get("description", "Telegram API setWebhook failed"))
        return payload

    def mark_update_processed(self, *, success: bool) -> None:
        self.last_update_at = timezone.now()
        if success:
            self.updates_count += 1
        else:
            self.errors_count += 1
        self.save(update_fields=["last_update_at", "updates_count", "errors_count", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.ensure_webhook_secret()
        super().save(*args, **kwargs)


class BotDeployment(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name="deployments")
    version = models.PositiveIntegerField()
    file_archive = models.FileField(storage=deployment_storage, upload_to="")
    deployed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("bot", "version")
        ordering = ["-deployed_at"]

    def __str__(self) -> str:
        return f"{self.bot.slug} v{self.version}"

    @staticmethod
    def _safe_extract(zip_ref: zipfile.ZipFile, target_dir: Path) -> None:
        root = target_dir.resolve()
        for member in zip_ref.infolist():
            member_path = (target_dir / member.filename).resolve()
            if root not in member_path.parents and member_path != root:
                raise ValidationError("Unsafe archive path detected")
        zip_ref.extractall(target_dir)

    def _cleanup_old_versions(self, keep_count: int = 3) -> None:
        old_deployments = self.bot.deployments.exclude(id=self.id).order_by("-version")
        for deployment in old_deployments[keep_count - 1 :]:
            deploy_dir = settings.BOTS_STORAGE_ROOT / self.bot.slug / f"v{deployment.version}"
            if deploy_dir.exists():
                shutil.rmtree(deploy_dir)

    def deploy(self) -> Path:
        if self.file_archive.size > MAX_ARCHIVE_SIZE_BYTES:
            raise ValidationError("Archive too large")

        target_dir = settings.BOTS_STORAGE_ROOT / self.bot.slug / f"v{self.version}"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(self.file_archive.path, "r") as zip_ref:
            self._safe_extract(zip_ref, target_dir)

        if not (target_dir / "bot.py").exists():
            raise ValidationError("Archive must contain bot.py")

        self.bot.code_path = str(target_dir)
        self.bot.code_version = self.version
        self.bot.save(update_fields=["code_path", "code_version", "updated_at"])
        self._cleanup_old_versions()
        return target_dir
