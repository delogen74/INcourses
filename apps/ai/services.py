from apps.content.models import ContentPlan, DraftPost, Topic


class AIProvider:
    def generate_plan(self, topics):
        titles = ', '.join(topic.title for topic in topics)
        return f'Стратегия публикаций по темам: {titles}'

    def generate_draft(self, topic: Topic):
        return {
            'title': f'Пост: {topic.title}',
            'content': f'<p>Черновик по теме: <strong>{topic.title}</strong></p>',
            'hashtags': '#inkhaip #smm',
        }


def create_content_plan(topic_ids, actor=None):
    topics = Topic.objects.filter(id__in=topic_ids)
    provider = AIProvider()
    strategy = provider.generate_plan(topics)
    return ContentPlan.objects.create(period='Неделя', strategy_text=strategy, generated_by=actor, generated_provider='stub-ai')


def create_draft_for_topic(topic, actor=None):
    provider = AIProvider()
    payload = provider.generate_draft(topic)
    return DraftPost.objects.create(topic=topic, created_by=actor, updated_by=actor, **payload)
