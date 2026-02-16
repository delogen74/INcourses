import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('content', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('platform', models.CharField(choices=[('vk', 'VK'), ('telegram', 'Telegram'), ('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('youtube', 'YouTube')], max_length=20)),
                ('kind', models.CharField(choices=[('default', 'Обычный'), ('notifications', 'Уведомления')], default='default', max_length=20)),
                ('display_name', models.CharField(max_length=255)),
                ('credentials_encrypted', models.BinaryField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'verbose_name': 'Подключение соцсети',
                'verbose_name_plural': 'Подключения соцсетей',
                'indexes': [models.Index(fields=['platform', 'kind', 'is_active'], name='social_soci_platfor_8fdbf2_idx')],
            },
        ),
        migrations.CreateModel(
            name='SocialPost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('platform', models.CharField(choices=[('vk', 'VK'), ('telegram', 'Telegram'), ('instagram', 'Instagram'), ('tiktok', 'TikTok'), ('youtube', 'YouTube')], max_length=20)),
                ('idempotency_key', models.CharField(max_length=64, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Ожидает'), ('scheduled', 'Запланирован'), ('publishing', 'Публикуется'), ('published', 'Опубликован'), ('failed', 'Ошибка')], default='pending', max_length=20)),
                ('scheduled_at', models.DateTimeField()),
                ('publishing_token', models.UUIDField(blank=True, null=True)),
                ('publishing_started_at', models.DateTimeField(blank=True, null=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('external_id', models.CharField(blank=True, max_length=255)),
                ('error_message', models.TextField(blank=True)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('publish_version', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('draft_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_posts', to='content.draftpost')),
                ('social_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social.socialaccount')),
            ],
            options={'verbose_name': 'Публикация', 'verbose_name_plural': 'Очередь публикаций'},
        ),
        migrations.AddConstraint(
            model_name='socialpost',
            constraint=models.UniqueConstraint(fields=('draft_post', 'platform', 'social_account', 'scheduled_at'), name='uniq_draft_platform_account_schedule'),
        ),
    ]
