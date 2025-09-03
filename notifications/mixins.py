from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from workshop.models import Workshop

from drf_spectacular.utils import extend_schema

from notifications.models import InternalNotification, ExternalNotification
from notifications.serializers import (
    InternalNotificatinoReadSerializer,
    InternalNotificationWriteSerializer,
    ExternalNotificationReadSerializer
)

from ecouture.serializers import (
    NotFound404ResponseSerializer, ValidationError400Serializer
)


class InternaNotificationMixin:
    """
    Mixin for handling internal notifications.
    """

    @extend_schema(
        methods=['get'],
        summary="Voir les notifications internes",
        description="Voir les notifications internes",
        responses={
            200: InternalNotificatinoReadSerializer(many=True),
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='internal',
        url_name='internal-get',
        permission_classes=[IsAuthenticated]
    )
    def internal_notification(self, request: Request, *args, **kwargs):
        """
        Retrieve or update internal notifications for the authenticated user.
        """
        user = request.user
        if request.method == 'GET':
            notifications = user.notifications.filter(is_read=False)
            page = self.paginate_queryset(notifications)
            serializer = InternalNotificatinoReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        raise ValidationError("Method not allowed. Use GET.")

    @extend_schema(
        methods=['patch'],
        summary="Modifier une notification interne",
        description="Modifier une notification interne",
        request=InternalNotificationWriteSerializer,
        responses={
            200: InternalNotificatinoReadSerializer,
            400: ValidationError400Serializer
        }
    )
    @action(
        detail=False,
        methods=['patch'],
        url_path='internal/(?P<notification_id>[^/.]+)',
        url_name='internal-update',
        permission_classes=[IsAuthenticated]
    )
    def update_internal_notification(self, request: Request, notification_id=None, *args, **kwargs):
        """
        Update an internal notification for the authenticated user.
        """
        notification = InternalNotification.objects.get(id=notification_id)
        serializer = InternalNotificationWriteSerializer(
            notification, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExternalNotificationMixin:
    """
    Mixin for handling external notifications.
    """

    @extend_schema(
        methods=['get'],
        summary="Voir les notifications externes",
        description="Voir les notifications externes",
        responses={
            200: ExternalNotificationReadSerializer(many=True),
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='external/(?P<workshop_pk>[^/.]+)',
        url_name='external',
        permission_classes=[IsAuthenticated])
    def external_notification(self, request: Request, workshop_pk=None, *args, **kwargs):
        """
        Retrieve external notifications for the authenticated user.
        """
        workshop = Workshop.objects.get(pk=workshop_pk)
        notifications = ExternalNotification.objects.filter(
            customer__workshop=workshop)
        serializer = ExternalNotificationReadSerializer(
            notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
