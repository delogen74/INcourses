from django.contrib import admin

from .models import SocialAccount, SocialPost


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'platform', 'kind', 'owner', 'is_active', 'created_at')
    list_filter = ('platform', 'kind', 'is_active')
    search_fields = ('display_name', 'owner__email')


@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ('draft_post', 'platform', 'status', 'scheduled_at', 'published_at', 'attempts')
    list_filter = ('platform', 'status')
    search_fields = ('draft_post__title', 'error_message')
