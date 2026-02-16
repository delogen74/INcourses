import uuid
from django.db import migrations, models
import django.db.models.deletion
import django_ckeditor_5.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('period', models.CharField(max_length=120)),
                ('strategy_text', models.TextField()),
                ('generated_provider', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
            ],
            options={'verbose_name': 'Контент-план', 'verbose_name_plural': 'Контент-планы'},
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255, verbose_name='Тема')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('new', 'Новая'), ('processing', 'В обработке'), ('planned', 'Запланирована'), ('rejected', 'Отклонена')], default='new', max_length=20)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
            ],
            options={'verbose_name': 'Тема', 'verbose_name_plural': 'Темы'},
        ),
        migrations.CreateModel(
            name='DraftPost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('content', django_ckeditor_5.fields.CKEditor5Field(config_name='default', verbose_name='Контент')),
                ('hashtags', models.CharField(blank=True, max_length=500)),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('waiting_approval', 'Ожидает согласования'), ('approved', 'Согласован'), ('rejected', 'Отклонен'), ('needs_revision', 'Нужна доработка')], default='draft', max_length=30)),
                ('review_comment', models.TextField(blank=True)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assets', models.ManyToManyField(blank=True, related_name='draft_posts', to='media.mediaasset')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_drafts', to='users.user')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drafts', to='content.topic')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_drafts', to='users.user')),
            ],
            options={'verbose_name': 'Черновик', 'verbose_name_plural': 'Черновики'},
        ),
    ]
