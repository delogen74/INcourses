from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialpost',
            name='review_comment',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='socialpost',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Ожидает'),
                    ('ready_for_approval', 'Готов к согласованию'),
                    ('approved', 'Согласован'),
                    ('rejected', 'Отклонён'),
                    ('needs_revision', 'Нужна доработка'),
                    ('scheduled', 'Запланирован'),
                    ('publishing', 'Публикуется'),
                    ('published', 'Опубликован'),
                    ('failed', 'Ошибка'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
