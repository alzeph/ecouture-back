from notifications.mixins import (
    InternaNotificationMixin,
    ExternalNotificationMixin
)
from rest_framework.viewsets import GenericViewSet
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class NotificationViewSet(
    InternaNotificationMixin,
    ExternalNotificationMixin,
    GenericViewSet
):
    """
    ViewSet for handling notifications.
    """
    pass


