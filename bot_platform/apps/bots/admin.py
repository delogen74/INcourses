from django import forms
from django.contrib import admin, messages

from apps.bot_runtime.manager import BotManager
from apps.bots.models import Bot, BotDeployment


class BotAdminForm(forms.ModelForm):
    raw_token = forms.CharField(required=False, help_text="Plain Telegram token")

    class Meta:
        model = Bot
        fields = ["name", "slug", "raw_token", "webhook_secret", "is_active", "config"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw_token = self.cleaned_data.get("raw_token")
        if raw_token:
            instance.set_token(raw_token)
        elif not instance.token:
            raise forms.ValidationError("raw_token is required for new bot")
        if commit:
            instance.save()
        return instance


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    form = BotAdminForm
    list_display = (
        "name",
        "slug",
        "is_active",
        "code_version",
        "updates_count",
        "errors_count",
        "last_update_at",
        "updated_at",
    )
    search_fields = ("name", "slug")
    readonly_fields = ("token_hash", "updates_count", "errors_count", "last_update_at")
    actions = ["restart_selected_bots", "activate_bots", "deactivate_bots", "register_webhooks"]

    @admin.action(description="Restart selected bots")
    def restart_selected_bots(self, request, queryset):
        for bot in queryset:
            BotManager.restart(bot)
        self.message_user(request, f"Restarted {queryset.count()} bot(s)", level=messages.SUCCESS)

    @admin.action(description="Activate selected bots")
    def activate_bots(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} bot(s)", level=messages.SUCCESS)

    @admin.action(description="Deactivate selected bots")
    def deactivate_bots(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} bot(s)", level=messages.WARNING)

    @admin.action(description="Register Telegram webhook for selected bots")
    def register_webhooks(self, request, queryset):
        success = 0
        failed = 0
        for bot in queryset:
            try:
                bot.register_webhook()
                success += 1
            except Exception as exc:
                failed += 1
                self.message_user(
                    request,
                    f"Webhook registration failed for {bot.slug}: {exc}",
                    level=messages.ERROR,
                )
        if success:
            self.message_user(request, f"Registered webhook for {success} bot(s)", level=messages.SUCCESS)
        if failed:
            self.message_user(request, f"Failed webhook registration for {failed} bot(s)", level=messages.WARNING)


@admin.register(BotDeployment)
class BotDeploymentAdmin(admin.ModelAdmin):
    list_display = ("bot", "version", "deployed_at")
    actions = ["deploy_selected"]

    @admin.action(description="Deploy selected archives")
    def deploy_selected(self, request, queryset):
        deployed = 0
        for deployment in queryset:
            deployment.deploy()
            deployed += 1
        self.message_user(request, f"Deployed {deployed} archive(s)", level=messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.deploy()
        self.message_user(request, f"Deployment v{obj.version} applied", level=messages.SUCCESS)
