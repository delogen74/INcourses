import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inkhaip_ai_smm.settings')

app = Celery('inkhaip_ai_smm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'publish-scheduled-social-posts-every-minute': {
        'task': 'apps.social.tasks.publish_scheduled_social_posts',
        'schedule': 60.0,
    },
    'recover-stuck-social-posts-every-5-minutes': {
        'task': 'apps.social.tasks.recover_stuck_social_posts',
        'schedule': 300.0,
    },
}
