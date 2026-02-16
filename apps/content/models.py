import uuid
import bleach
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field


ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'blockquote', 'img']


class TopicStatus(models.TextChoices):
    NEW = 'new', 'Новая'
    PROCESSING = 'processing', 'В обработке'
    PLANNED = 'planned', 'Запланирована'
    REJECTED = 'rejected', 'Отклонена'


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Тема'), max_length=255)
    description = models.TextField(_('Описание'), blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TopicStatus.choices, default=TopicStatus.NEW)

    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'


class ContentPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.CharField(max_length=120)
    strategy_text = models.TextField()
    generated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    generated_provider = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Контент-план'
        verbose_name_plural = 'Контент-планы'


class DraftStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    WAITING_APPROVAL = 'waiting_approval', 'Ожидает согласования'
    APPROVED = 'approved', 'Согласован'
    REJECTED = 'rejected', 'Отклонен'
    NEEDS_REVISION = 'needs_revision', 'Нужна доработка'


class DraftPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='drafts')
    title = models.CharField(max_length=255, blank=True)
    content = CKEditor5Field('Контент', config_name='default')
    hashtags = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=30, choices=DraftStatus.choices, default=DraftStatus.DRAFT)
    review_comment = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_drafts')
    updated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='updated_drafts')
    assets = models.ManyToManyField('media.MediaAsset', blank=True, related_name='draft_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Черновик'
        verbose_name_plural = 'Черновики'

    def clean(self):
        self.content = bleach.clean(self.content, tags=ALLOWED_TAGS, attributes={'a': ['href', 'title'], 'img': ['src', 'alt']})

    @transaction.atomic
    def transition_status(self, new_status, actor, comment=''):
        from apps.users.models import UserRole
        from apps.audit.services import log_event
        if actor and actor.role == UserRole.AI_AGENT:
            if not (self.status == DraftStatus.DRAFT and new_status == DraftStatus.WAITING_APPROVAL):
                raise ValidationError('AI-агент может переводить только draft -> waiting_approval')

        self.status = new_status
        self.review_comment = comment
        self.updated_by = actor
        self.save(update_fields=['status', 'review_comment', 'updated_by', 'updated_at'])
        log_event(actor=actor, action='draft.status_changed', entity=self, payload={'status': new_status, 'comment': comment})
