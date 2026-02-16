from celery import shared_task

from apps.content.models import Topic
from .services import create_content_plan, create_draft_for_topic


@shared_task
def ai_generate_content_plan(topic_ids):
    create_content_plan(topic_ids=topic_ids)


@shared_task
def ai_generate_drafts(topic_id):
    topic = Topic.objects.get(id=topic_id)
    create_draft_for_topic(topic)
