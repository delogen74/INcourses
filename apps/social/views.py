from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import decorators, exceptions, permissions, response, viewsets

from apps.audit.services import log_event
from apps.users.models import UserRole

from .models import SocialAccount, SocialPost
from .serializers import SocialAccountSerializer, SocialPostSerializer
from .services import check_redis_health


class SocialAccountViewSet(viewsets.ModelViewSet):
    queryset = SocialAccount.objects.all().order_by('-created_at')
    serializer_class = SocialAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            raise exceptions.PermissionDenied('AI-агент не имеет доступа к social accounts')
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == UserRole.OWNER:
            return qs.filter(owner=self.request.user)
        return qs.none()


class SocialPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SocialPost.objects.select_related('draft_post', 'social_account').all().order_by('-scheduled_at')
    serializer_class = SocialPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            raise exceptions.PermissionDenied('AI-агент не имеет доступа к social posts')
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        start = self.request.query_params.get('from')
        end = self.request.query_params.get('to')
        if start:
            qs = qs.filter(scheduled_at__date__gte=parse_date(start))
        if end:
            qs = qs.filter(scheduled_at__date__lte=parse_date(end))
        if self.request.user.role == UserRole.OWNER:
            qs = qs.filter(social_account__owner=self.request.user)
        else:
            qs = qs.none()
        return qs

    @decorators.action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        if request.user.role not in (UserRole.OWNER, UserRole.EDITOR):
            raise exceptions.PermissionDenied('Согласование доступно только owner/editor')

        social_post = self.get_object()
        review_status = request.data.get('status')
        comment = (request.data.get('comment') or '').strip()

        if review_status not in (
            SocialPost.Status.APPROVED,
            SocialPost.Status.REJECTED,
            SocialPost.Status.NEEDS_REVISION,
        ):
            raise exceptions.ValidationError({'status': 'Допустимые значения: approved, rejected, needs_revision'})
        if social_post.status != SocialPost.Status.READY_FOR_APPROVAL:
            raise exceptions.ValidationError({'status': 'Review доступен только из статуса ready_for_approval'})
        if not social_post.can_review_transition_to(review_status):
            raise exceptions.ValidationError({'status': 'Недопустимый переход статуса'})
        if review_status in (SocialPost.Status.REJECTED, SocialPost.Status.NEEDS_REVISION) and not comment:
            raise exceptions.ValidationError({'comment': 'Комментарий обязателен для отклонения и доработки'})

        social_post.status = review_status
        social_post.review_comment = comment
        social_post.save(update_fields=['status', 'review_comment', 'updated_at'])

        log_event(
            actor=request.user,
            action='social.review_status_changed',
            entity=social_post,
            payload={'status': review_status, 'comment': comment},
        )
        return response.Response(SocialPostSerializer(social_post).data)

    @decorators.action(detail=False, methods=['get'], url_path='metrics/summary')
    def metrics_summary(self, request):
        if request.user.role != UserRole.OWNER:
            raise exceptions.PermissionDenied('Доступ к метрикам только у owner')
        qs = self.filter_queryset(self.get_queryset())
        by_status = list(qs.values('status').annotate(total=Count('id')).order_by('status'))
        by_platform = list(qs.values('platform').annotate(total=Count('id')).order_by('platform'))
        failed_by_platform = list(
            qs.filter(status=SocialPost.Status.FAILED).values('platform').annotate(total=Count('id')).order_by('platform')
        )
        return response.Response({
            'total': qs.count(),
            'by_status': by_status,
            'by_platform': by_platform,
            'failed_by_platform': failed_by_platform,
        })

    @decorators.action(detail=False, methods=['get'], url_path='health')
    def health(self, request):
        if request.user.role != UserRole.OWNER:
            raise exceptions.PermissionDenied('Доступ к health только у owner')
        stuck_cutoff = timezone.now() - timezone.timedelta(minutes=getattr(settings, 'SOCIAL_PUBLISH_STUCK_TTL_MINUTES', 15))
        stuck_count = SocialPost.objects.filter(status=SocialPost.Status.PUBLISHING, updated_at__lt=stuck_cutoff).count()
        return response.Response({
            'redis_ok': check_redis_health(),
            'stuck_publishing_count': stuck_count,
        })
