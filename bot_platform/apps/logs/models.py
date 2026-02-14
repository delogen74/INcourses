from django.db import models


class BotLog(models.Model):
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"

    LEVEL_CHOICES = [
        (LEVEL_INFO, "Info"),
        (LEVEL_WARNING, "Warning"),
        (LEVEL_ERROR, "Error"),
    ]

    bot = models.ForeignKey("bots.Bot", on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default=LEVEL_INFO)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    traceback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.bot.slug} [{self.level}]"
