# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('bots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('ERROR', 'Error')], default='INFO', max_length=16)),
                ('message', models.TextField()),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('traceback', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='bots.bot')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
