# Telegram Bot Platform

Production-focused Django-платформа для управления Telegram-ботами через webhook, Celery и Redis.

## Что исправлено для production-базы
- Webhook URL больше не содержит Telegram token: используется `POST /telegram/webhook/<slug>/`.
- Валидация секрета выполняется через `X-Telegram-Bot-Api-Secret-Token` (пер-ботовый secret, fallback на global).
- Добавлена защита от Zip Slip при распаковке архивов.
- Включены `SECURE_PROXY_SSL_HEADER`, secure cookies и `SECURE_SSL_REDIRECT` в non-debug.
- Убраны wildcard-хосты по умолчанию.
- Добавлен rate limiting на webhook через `django-ratelimit` (по IP и по bot slug).
- Добавлена проверка `bot.is_active` в webhook (inactive -> 403).
- Добавлена проверка размера ZIP-архива (до 20MB).
- Добавлен `/health/` (DB + Redis).
- Добавлены метрики `last_update_at`, `updates_count`, `errors_count` в `Bot`.
- В админке добавлено действие `Register webhook` (вызов Telegram setWebhook).
- Добавлены real unit-файлы `systemd` и `nginx` конфиг.

## Возможности
- Управление ботами в Django Admin (Jazzmin).
- Загрузка ZIP-архивов с кодом бота, деплой версий, автоочистка старых версий (хранится максимум 3).
- Асинхронная обработка updates через Celery с timeout.
- Логирование в БД (`BotLog`) и файл `bot_platform.log`.

## Важные endpoint'ы
- `POST /telegram/webhook/<slug>/`
- `GET /health/`

## Структура
```text
bot_platform/
├── core/
├── apps/
│   ├── bots/
│   ├── bot_runtime/
│   ├── logs/
│   ├── users/
│   └── system/
├── deploy/
│   ├── nginx/bot-platform.conf
│   └── systemd/*.service
├── bots_storage/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Локальный запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Celery worker:
```bash
celery -A core worker -l info
```

## Docker
```bash
docker compose up --build
```

## .env
См. `.env.example`:
- `DJANGO_ALLOWED_HOSTS=185.192.247.229,bot.yourdomain.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://bot.yourdomain.com`
- `DATABASE_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `TELEGRAM_WEBHOOK_BASE_URL`
- `BOT_TOKEN_ENCRYPTION_KEY` (обязателен, без fallback)
- `DJANGO_SECRET_KEY` (обязателен, без fallback)

## Подключение Telegram webhook
Для каждого `Bot` используйте:
- URL: `https://bot.yourdomain.com/telegram/webhook/<bot-slug>/`
- secret_token: `bot.webhook_secret` из админки

```bash
curl -X POST "https://api.telegram.org/bot<telegram_token>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://bot.yourdomain.com/telegram/webhook/<bot-slug>/",
    "secret_token": "<bot_webhook_secret>"
  }'
```

## Production deployment (VDS)
1. Создайте отдельного пользователя `botplatform`.
2. Запретите root login по SSH, используйте только ключи.
3. Настройте UFW/iptables и fail2ban.
4. Закройте внешний доступ к `5432` и `6379`.
5. Установите и активируйте systemd unit-файлы из `deploy/systemd/`.
6. Подключите nginx конфиг из `deploy/nginx/bot-platform.conf`.
7. Выпустите сертификат certbot.

## Failover (рекомендация)
Текущий compose ориентирован на single-node. Для реального failover используйте:
- PostgreSQL HA (Patroni / managed DB).
- Redis Sentinel/Cluster.
- Разделение web/celery по разным узлам.

## Тесты
```bash
python manage.py test
```
