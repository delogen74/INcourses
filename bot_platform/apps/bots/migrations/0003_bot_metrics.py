from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bots", "0002_bot_webhook_secret"),
    ]

    operations = [
        migrations.AddField(
            model_name="bot",
            name="errors_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="bot",
            name="last_update_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bot",
            name="updates_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
