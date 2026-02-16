from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import decorators, exceptions, permissions, response, status, viewsets

from apps.social.models import SocialAccount, SocialPost
from apps.social.services import build_social_post_idempotency_key
from apps.social.serializers import SocialPostSerializer
from apps.users.models import UserRole

from .models import ContentPlan, DraftPost, DraftStatus, Topic
from .serializers import (
    ContentPlanSerializer,
    DraftPostAISerializer,
    DraftPostHumanSerializer,
    TopicSerializer,
)


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all().order_by('-created_at')
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            if self.action in ('list', 'retrieve') and 'ai:read_topics' in self.request.service_token.scopes:
                return [permissions.IsAuthenticated()]
            raise exceptions.PermissionDenied('Недостаточно scope для этой операции.')
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContentPlanViewSet(viewsets.ModelViewSet):
    queryset = ContentPlan.objects.all().order_by('-created_at')
    serializer_class = ContentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            if self.action in ('create', 'update', 'partial_update') and 'ai:write_plans' in self.request.service_token.scopes:
                return [permissions.IsAuthenticated()]
            if self.action in ('list', 'retrieve'):
                raise exceptions.PermissionDenied('AI-агент не может читать контент-планы.')
            raise exceptions.PermissionDenied('Недостаточно scope для этой операции.')
        return super().get_permissions()


class DraftPostViewSet(viewsets.ModelViewSet):
    queryset = DraftPost.objects.all().order_by('-created_at').prefetch_related('assets')
    serializer_class = DraftPostHumanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if getattr(self.request, 'service_token', None):
            return DraftPostAISerializer
        return DraftPostHumanSerializer

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            if self.action in ('list', 'retrieve') and 'ai:read_drafts' in self.request.service_token.scopes:
                return [permissions.IsAuthenticated()]
            if self.action in ('create', 'update', 'partial_update') and 'ai:write_drafts' in self.request.service_token.scopes:
                return [permissions.IsAuthenticated()]
            raise exceptions.PermissionDenied('Недостаточно scope для этой операции.')
        return super().get_permissions()

    @decorators.action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        draft = self.get_object()
        draft.transition_status(DraftStatus.APPROVED, request.user)
        return response.Response(DraftPostHumanSerializer(draft, context={'request': request}).data)

    @decorators.action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        draft = self.get_object()
        draft.transition_status(DraftStatus.REJECTED, request.user, request.data.get('comment', ''))
        return response.Response(DraftPostHumanSerializer(draft, context={'request': request}).data)

    @decorators.action(detail=True, methods=['post'], url_path='needs-revision')
    def needs_revision(self, request, pk=None):
        draft = self.get_object()
        draft.transition_status(DraftStatus.NEEDS_REVISION, request.user, request.data.get('comment', ''))
        return response.Response(DraftPostHumanSerializer(draft, context={'request': request}).data)

    @decorators.action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        draft = self.get_object()
        scheduled_at_raw = request.data.get('scheduled_at')
        scheduled_at = parse_datetime(scheduled_at_raw) if scheduled_at_raw else None

        if not scheduled_at:
            raise exceptions.ValidationError({'scheduled_at': 'Некорректный datetime. Используйте ISO 8601.'})
        if timezone.is_naive(scheduled_at):
            raise exceptions.ValidationError({'scheduled_at': 'Datetime должен быть timezone-aware.'})

        scheduled_at = scheduled_at.replace(microsecond=0)

        targets = request.data.get('targets', [])
        if not isinstance(targets, list) or not targets:
            raise exceptions.ValidationError({'targets': 'Укажите хотя бы одну цель публикации.'})

        validated_targets = []
        for idx, target in enumerate(targets):
            if not isinstance(target, dict):
                raise exceptions.ValidationError({'targets': f'Элемент #{idx + 1} должен быть объектом'})
            platform = target.get('platform')
            social_account_id = target.get('social_account_id')
            if not platform or not social_account_id:
                raise exceptions.ValidationError({'targets': f'Элемент #{idx + 1} должен содержать platform и social_account_id'})
            try:
                account = SocialAccount.objects.get(id=social_account_id, is_active=True)
            except SocialAccount.DoesNotExist as exc:
                raise exceptions.ValidationError({'targets': f'Элемент #{idx + 1}: аккаунт не найден или неактивен'}) from exc
            if account.platform != platform:
                raise exceptions.ValidationError({'targets': f'Элемент #{idx + 1}: platform не совпадает с social account'})
            validated_targets.append((platform, account.id))

        if draft.status != DraftStatus.APPROVED and request.user.role in (UserRole.OWNER, UserRole.EDITOR):
            draft.transition_status(DraftStatus.APPROVED, request.user)

        with transaction.atomic():
            social_posts = []
            for platform, account_id in validated_targets:
                idempotency_key = build_social_post_idempotency_key(
                    draft_post_id=draft.id,
                    social_account_id=account_id,
                    platform=platform,
                    scheduled_at=scheduled_at,
                )
                social_post, _ = SocialPost.objects.get_or_create(
                    draft_post=draft,
                    platform=platform,
                    social_account_id=account_id,
                    scheduled_at=scheduled_at,
                    defaults={
                        'status': SocialPost.Status.SCHEDULED,
                        'idempotency_key': idempotency_key,
                    },
                )
                social_posts.append(social_post)
            draft.scheduled_at = scheduled_at
            draft.save(update_fields=['scheduled_at', 'updated_at'])

        return response.Response(SocialPostSerializer(social_posts, many=True).data, status=status.HTTP_201_CREATED)
