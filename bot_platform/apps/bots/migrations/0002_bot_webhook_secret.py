import secrets

from django.db import migrations, models


def populate_webhook_secret(apps, schema_editor):
    Bot = apps.get_model("bots", "Bot")
    for bot in Bot.objects.filter(webhook_secret=""):
        bot.webhook_secret = secrets.token_urlsafe(32)
        bot.save(update_fields=["webhook_secret"])


class Migration(migrations.Migration):

    dependencies = [
        ("bots", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bot",
            name="webhook_secret",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunPython(populate_webhook_secret, migrations.RunPython.noop),
    ]
