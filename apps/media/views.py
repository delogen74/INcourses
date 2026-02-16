from rest_framework import exceptions, permissions, viewsets

from .models import MediaAsset
from .serializers import MediaAssetSerializer


class MediaAssetViewSet(viewsets.ModelViewSet):
    serializer_class = MediaAssetSerializer
    queryset = MediaAsset.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if getattr(self.request, 'service_token', None):
            raise exceptions.PermissionDenied('AI-агент не имеет доступа к media assets')
        return super().get_permissions()
