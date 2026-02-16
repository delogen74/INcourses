# INKHAIP AI SMM Manager

Бэкенд на Django 5 для контент-воркфлоу: темы → черновики от ИИ → согласование → автопостинг в VK/Telegram.

## Стек
- Django 5 + DRF
- JWT + сервисные токены (`X-SERVICE-TOKEN`)
- Celery + Redis + Postgres
- Админка `django-unfold` (RU)
- WYSIWYG (`django-ckeditor-5`) + медиа-ассеты

## Быстрый старт
```bash
cp .env.example .env
# Сгенерируйте ENCRYPTION_KEY и вставьте в .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
docker compose up --build
```

После запуска:
- API: `http://localhost:8000/api/`
- Swagger: `http://localhost:8000/api/docs/`
- Admin: `http://localhost:8000/admin/`

## Сервисный токен для AI-агента
1. Создайте пользователя с ролью `ai_agent`.
2. Выполните команду:
```bash
python manage.py create_service_token --name ai-main --user-email ai@example.com --scopes ai:read_topics ai:read_drafts ai:write_drafts ai:write_plans
```
3. Сохраните выведенный raw-токен (показывается один раз).

## Уведомления в Telegram
Уведомления отправляются асинхронно Celery-задачей `send_telegram_notification` при событиях:
- создание черновика (`🆕`),
- правки черновика по важным полям (`✏️`),
- успешная публикация (`✅`).

Для включения уведомлений создайте в админке `SocialAccount`:
- `platform=telegram`
- `kind=notifications`
- `is_active=true`
- credentials JSON:
```json
{"bot_token": "123:ABC", "chat_id": "@channel_name"}
```

## Подключение VK
1. Создайте `SocialAccount` с платформой `vk`.
2. Передайте credentials JSON:
```json
{"group_id": "123456", "access_token": "vk_token"}
```

## Подключение Telegram для постинга
1. Создайте бота и добавьте его админом канала.
2. Создайте `SocialAccount` с платформой `telegram` и `kind=default`.
3. Передайте credentials JSON:
```json
{"bot_token": "123:ABC", "chat_id": "@channel_name"}
```

## Архитектура коннекторов
- Реализовано: `VKConnector`, `TelegramConnector`
- Заглушки: Instagram/TikTok/YouTube (готовы к расширению)

## Автопостинг
Celery Beat каждую минуту запускает задачу `publish_scheduled_social_posts`, которая атомарно резервирует элементы очереди (`pending/scheduled`) и публикует через соответствующий connector.

## Надёжность publish pipeline
- `idempotency_key` у `SocialPost` для защиты от дублей.
- Recovery-задача `recover_stuck_social_posts` (каждые 5 минут) возвращает зависшие `PUBLISHING` в `PENDING` или переводит в `FAILED`.
- Redis-lock `lock:socialpost:{id}` защищает от конкурентной публикации одним и тем же постом.
- Summary endpoint: `GET /api/social-posts/metrics/summary/` (агрегаты по статусам/платформам, доступ только owner).
- Health endpoint: `GET /api/social-posts/health/` (redis + stuck publishing count, доступ только owner).

## Тесты
```bash
pip install -r requirements.txt
ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" pytest -q
```

## HTTPS + фронтенд через Nginx
- Фронтенд собирается отдельным контейнером `frontend` (Vite build + nginx static).
- Внешний reverse proxy `nginx` (см. `deploy/nginx/nginx.conf`) делает:
  - `80 -> 301 https`
  - `/api/ -> web:8000`
  - `/ -> frontend:80`
- Для production замените `yourdomain.com` в `deploy/nginx/nginx.conf` и смонтируйте Let's Encrypt сертификаты в `./certbot/conf`.
