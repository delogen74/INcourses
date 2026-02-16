from django.contrib import admin, messages

from .models import ContentPlan, DraftPost, DraftStatus, Topic


@admin.action(description='Согласовать выбранные')
def approve_selected(modeladmin, request, queryset):
    success = 0
    for draft in queryset:
        try:
            draft.transition_status(DraftStatus.APPROVED, request.user)
            success += 1
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f'Ошибка для {draft.id}: {exc}')
    messages.success(request, f'Согласовано: {success}')


@admin.action(description='Отклонить выбранные')
def reject_selected(modeladmin, request, queryset):
    success = 0
    for draft in queryset:
        try:
            draft.transition_status(DraftStatus.REJECTED, request.user, 'Отклонено через bulk action в админке')
            success += 1
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f'Ошибка для {draft.id}: {exc}')
    messages.success(request, f'Отклонено: {success}')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')


@admin.register(ContentPlan)
class ContentPlanAdmin(admin.ModelAdmin):
    list_display = ('period', 'generated_by', 'created_at')
    search_fields = ('period', 'strategy_text')


@admin.register(DraftPost)
class DraftPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'status', 'scheduled_at', 'created_by', 'created_at')
    list_filter = ('status', 'created_at', 'scheduled_at')
    search_fields = ('topic__title', 'content', 'status', 'created_by__email')
    filter_horizontal = ('assets',)
    actions = [approve_selected, reject_selected]
