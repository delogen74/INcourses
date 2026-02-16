import uuid
from django.db import models


class MediaAsset(models.Model):
    class AssetType(models.TextChoices):
        IMAGE = 'image', 'Изображение'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='assets/%Y/%m/%d/')
    type = models.CharField(max_length=20, choices=AssetType.choices, default=AssetType.IMAGE)
    uploaded_by = models.ForeignKey('users.User', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'

    def __str__(self):
        return self.file.name
