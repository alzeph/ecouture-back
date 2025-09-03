from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from workshop.views import WorkshopViewSet
from haberdashery.views import HaberdasheryViewSet
from notifications.views import NotificationViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


router = DefaultRouter()
router.register(r'user', UserViewSet, basename='users')
router.register(r'workshop', WorkshopViewSet, basename='workshops')
router.register(r'haberdashery', HaberdasheryViewSet, basename='haberdasheries')
router.register(r'notification', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path("api/auth/token/", TokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path("api/auth/token/refresh/",
         TokenRefreshView.as_view(), name="token_refresh"),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/',
         SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
