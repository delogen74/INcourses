from django.contrib import admin

from apps.logs.models import BotLog


@admin.register(BotLog)
class BotLogAdmin(admin.ModelAdmin):
    list_display = ("bot", "level", "message", "created_at")
    list_filter = ("level", "created_at")
    search_fields = ("message", "bot__slug")
    readonly_fields = ("bot", "level", "message", "payload", "traceback", "created_at")
