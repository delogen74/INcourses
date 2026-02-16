from rest_framework import serializers
from .models import MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = ('id', 'file', 'url', 'type', 'uploaded_by', 'created_at')
        read_only_fields = ('uploaded_by', 'created_at', 'url')

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['uploaded_by'] = user if getattr(user, 'is_authenticated', False) else None
        return super().create(validated_data)
