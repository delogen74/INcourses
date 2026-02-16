from django.db import transaction
from rest_framework import serializers

from apps.social.tasks import send_telegram_notification

from .models import ContentPlan, DraftPost, Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ('id', 'title', 'description', 'created_by', 'created_at', 'status')
        read_only_fields = ('created_by', 'created_at')


class ContentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentPlan
        fields = ('id', 'period', 'strategy_text', 'generated_by', 'generated_provider', 'created_at')
        read_only_fields = ('created_at',)


class DraftPostHumanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftPost
        fields = (
            'id', 'topic', 'title', 'content', 'hashtags', 'status', 'review_comment', 'scheduled_at',
            'created_by', 'updated_by', 'assets', 'created_at', 'updated_at',
        )
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        instance = super().create(validated_data)
        transaction.on_commit(
            lambda: send_telegram_notification.delay(
                f'🆕 Новый черновик\nТема: {instance.topic.title}\nЗаголовок: {instance.title or "Без заголовка"}\nАвтор: {instance.created_by.email if instance.created_by else "AI"}'
            )
        )
        return instance

    def update(self, instance, validated_data):
        changed = any(field in validated_data for field in {'title', 'content', 'hashtags', 'assets'})
        validated_data['updated_by'] = self.context['request'].user
        instance = super().update(instance, validated_data)
        if changed:
            transaction.on_commit(
                lambda: send_telegram_notification.delay(
                    f'✏️ Внесены правки\nТема: {instance.topic.title}\nЗаголовок: {instance.title or "Без заголовка"}'
                )
            )
        return instance


class DraftPostAISerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftPost
        fields = ('id', 'topic', 'title', 'content', 'hashtags', 'assets', 'status', 'created_by', 'updated_by', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'created_by', 'updated_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        instance = super().create(validated_data)
        transaction.on_commit(
            lambda: send_telegram_notification.delay(
                f'🆕 Новый черновик\nТема: {instance.topic.title}\nЗаголовок: {instance.title or "Без заголовка"}\nАвтор: {instance.created_by.email if instance.created_by else "AI"}'
            )
        )
        return instance

    def update(self, instance, validated_data):
        changed = any(field in validated_data for field in {'title', 'content', 'hashtags', 'assets'})
        validated_data.pop('status', None)
        validated_data.pop('review_comment', None)
        validated_data.pop('scheduled_at', None)
        validated_data['updated_by'] = self.context['request'].user
        instance = super().update(instance, validated_data)
        if changed:
            transaction.on_commit(
                lambda: send_telegram_notification.delay(
                    f'✏️ Внесены правки\nТема: {instance.topic.title}\nЗаголовок: {instance.title or "Без заголовка"}'
                )
            )
        return instance
