from rest_framework import viewsets
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

from users.mixins import UserMixin, UserPasswordMixin
from users.serializers import (
    UserReadSerializer, UserWriteSerializer, UserPasswordWrite,
    GroupReadSerializer, PermissionReadSerializer
)

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(UserMixin, UserPasswordMixin, viewsets.GenericViewSet):
    """
    ViewSet pour la gestion des utilisateurs et la réinitialisation des mots de passe.
    Combine les actions de UserMixin et UserPasswordMixin.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
