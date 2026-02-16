from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import ServiceToken, UserRole


class ServiceTokenAuthentication(BaseAuthentication):
    header_name = 'HTTP_X_SERVICE_TOKEN'

    def authenticate(self, request):
        raw_token = request.META.get(self.header_name)
        if not raw_token:
            return None

        token_hash = ServiceToken.hash_token(raw_token)
        try:
            token = ServiceToken.objects.select_related('service_user').get(token_hash=token_hash, is_active=True)
        except ServiceToken.DoesNotExist as exc:
            raise AuthenticationFailed('Некорректный сервисный токен.') from exc

        if token.service_user.role != UserRole.AI_AGENT:
            raise AuthenticationFailed('Сервисный токен может принадлежать только пользователю с ролью ai_agent.')

        token.last_used_at = timezone.now()
        token.save(update_fields=['last_used_at'])

        request.service_token = token
        return (token.service_user, token)
