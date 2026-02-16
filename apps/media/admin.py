from django.contrib import admin
from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'uploaded_by', 'created_at')
    search_fields = ('file',)
    list_filter = ('type',)
