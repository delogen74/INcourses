from django.core.management.base import BaseCommand, CommandError

from apps.users.models import ServiceToken, User, UserRole


class Command(BaseCommand):
    help = 'Создать сервисный токен для ai_agent пользователя.'

    def add_arguments(self, parser):
        parser.add_argument('--name', required=True)
        parser.add_argument('--user-email', required=True)
        parser.add_argument('--scopes', nargs='+', required=True)

    def handle(self, *args, **options):
        email = options['user_email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise CommandError(f'Пользователь {email} не найден') from exc

        if user.role != UserRole.AI_AGENT:
            raise CommandError('Сервисный токен можно создать только для пользователя с ролью ai_agent')

        raw, token_hash = ServiceToken.generate_token()
        token = ServiceToken.objects.create(
            service_user=user,
            name=options['name'],
            token_hash=token_hash,
            scopes=options['scopes'],
        )
        self.stdout.write(self.style.SUCCESS(f'Создан token {token.id}'))
        self.stdout.write(self.style.WARNING('Сохраните raw token, он больше не будет показан:'))
        self.stdout.write(raw)
