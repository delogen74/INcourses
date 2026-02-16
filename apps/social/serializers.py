import bleach
from rest_framework import serializers

from .models import SocialAccount, SocialPost


class SocialAccountSerializer(serializers.ModelSerializer):
    credentials = serializers.JSONField(write_only=True, required=True)

    class Meta:
        model = SocialAccount
        fields = ('id', 'owner', 'platform', 'kind', 'display_name', 'credentials', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        creds = validated_data.pop('credentials')
        instance = SocialAccount(**validated_data)
        instance.set_credentials(creds)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        creds = validated_data.pop('credentials', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if creds is not None:
            instance.set_credentials(creds)
        instance.save()
        return instance


class SocialPostSerializer(serializers.ModelSerializer):
    draft_post_title = serializers.CharField(source='draft_post.title', read_only=True)
    draft_content_preview = serializers.SerializerMethodField()

    class Meta:
        model = SocialPost
        fields = '__all__'

    def get_draft_content_preview(self, obj: SocialPost) -> str:
        plain = bleach.clean(obj.draft_post.content or '', tags=[], strip=True)
        return plain[:240]
