from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.content.views import TopicViewSet, ContentPlanViewSet, DraftPostViewSet
from apps.social.views import SocialAccountViewSet, SocialPostViewSet
from apps.media.views import MediaAssetViewSet

router = DefaultRouter()
router.register('topics', TopicViewSet, basename='topic')
router.register('content-plans', ContentPlanViewSet, basename='content-plan')
router.register('draft-posts', DraftPostViewSet, basename='draft-post')
router.register('social-accounts', SocialAccountViewSet, basename='social-account')
router.register('social-posts', SocialPostViewSet, basename='social-post')
router.register('media/assets', MediaAssetViewSet, basename='media-asset')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include(router.urls)),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
