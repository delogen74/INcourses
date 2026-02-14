# Generated manually
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('token', models.TextField(help_text='Encrypted telegram token')),
                ('token_hash', models.CharField(editable=False, max_length=64, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('code_version', models.PositiveIntegerField(default=0)),
                ('code_path', models.CharField(blank=True, max_length=512)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BotDeployment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveIntegerField()),
                ('file_archive', models.FileField(upload_to='')),
                ('deployed_at', models.DateTimeField(auto_now_add=True)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='bots.bot')),
            ],
            options={'ordering': ['-deployed_at'], 'unique_together': {('bot', 'version')}},
        ),
    ]
