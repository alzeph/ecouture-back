from datetime import timedelta
from django.utils import timezone
import secrets
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from users.models import UserPasswordReset

from users.serializers import (
    GroupReadSerializer, PermissionReadSerializer,
    UserPasswordWrite, UserReadSerializer, UserWriteSerializer,
    
)
from users.models import GROUPS
from ecouture.serializers import ExistsResponseSerializer, VerifyFieldSerializer
from workshop.serializers.read import WorkerReadSerializer

from drf_spectacular.utils import extend_schema
User = get_user_model()


class UserMixin:
    
    def _verify_field(self, field_name: str, value: str, exclude_value: str = None):
        """
        Méthode générique pour vérifier si une valeur existe sur un champ spécifique.
        """
        if not value:
            return Response({"detail": f"{field_name} is required"}, status=status.HTTP_400_BAD_REQUEST)

        users_qs = User.objects.all()
        if exclude_value:
            users_qs = users_qs.exclude(**{field_name: exclude_value})

        exists = users_qs.filter(**{field_name: value}).exists()
        return Response({"exists": exists})

    @extend_schema(
        summary="Vérifie si un email existe",
        description="Permet de vérifier si un email est déjà utilisé. Possibilité d'exclure un email existant.",
        request=VerifyFieldSerializer,
        responses={200: ExistsResponseSerializer}
    )
    @action(
        detail=False,
        methods=['post'],
        url_path=r'verify-email',
        url_name='user-verify-email',
        permission_classes=[AllowAny]
    )
    def verify_email(self, request: Request, pk=None):
        """
        Vérifie si un email existe, possibilité d'exclure un email.
        """
        verify_email = request.data.get('verify')
        exclude_email = request.data.get('exclude')
        return self._verify_field('email', verify_email, exclude_email)

    @extend_schema(
        summary="Vérifie si un phone existe",
        description="Permet de vérifier si un phone est déjà utilisé. Possibilité d'exclure un phone existant.",
        request=VerifyFieldSerializer,
        responses={200: ExistsResponseSerializer}
    )
    @action(
        detail=False,
        methods=['post'],
        url_path=r'verify-phone',
        url_name='user-verify-phone',
        permission_classes=[AllowAny]
    )
    def verify_phone(self, request: Request, pk=None):
        """
        Vérifie si un numéro de téléphone existe, possibilité d'exclure un numéro.
        """
        verify_phone = request.data.get('verify')
        exclude_phone = request.data.get('exclude')
        return self._verify_field('phone', verify_phone, exclude_phone)

    @extend_schema(
        summary="metre a jour un utilisateur",
        description="permet de mettre à jour un utilisateur",
        request=UserWriteSerializer,
        responses={200: UserReadSerializer}
    )
    @action(
        detail=False,
        methods=['patch', 'put'],
        url_path=r'modify/(?P<user_id>[^/.]+)',
        url_name='user-modify',
        permission_classes=[IsAuthenticated]
    )
    def modify_users(self, request: Request, pk=None, user_id=None):
        """
        Modifier les informations d'un utilisateur.
        """
        try:
            _user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserWriteSerializer(
            _user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

        return Response(UserReadSerializer(user).data)

    @extend_schema(
        summary="recuperer les infos d'un utilisateur",
        description="permet de recuperer les infos d'un utilisateur",
        request=None,
        responses={200: WorkerReadSerializer}
    )
    @action(
        detail=False,
        methods=['get'],
        url_path=r'info-detail',
        url_name='user-modify',
        permission_classes=[IsAuthenticated]
    )
    def user_info_detail(self, request: Request, pk=None):
        """
        Récupère les informations détaillées d'un utilisateur.
        """
        user = request.user.worker
        return Response(WorkerReadSerializer(user).data)

    @extend_schema(
        summary="recuperer la liste des groupes",
        description="permet de mettre recuperer la liste des groupes",
        request=None,
        responses={200: GroupReadSerializer(many=True)}
    )
    @action(
        detail=False,
        methods=['get'],
        url_path=r'groups',
        url_name='user-group',
        permission_classes=[AllowAny]
    )
    def groups_list(self, request: Request, pk=None):
        """
        Liste tous les groupes.
        """
        groups = Group.objects.all()
        return Response(GroupReadSerializer(groups, many=True).data)

    @extend_schema(
        summary="recuperer la liste des permissions",
        description="permet de mettre recuperer la liste des permissions",
        request=None,
        responses={200: PermissionReadSerializer(many=True)}
    )
    @action(
        detail=False,
        methods=['get'],
        url_path=r'user-permissions',
        url_name='user-permission',
        permission_classes=[AllowAny]
    )
    def permissions_list(self, request: Request, pk=None):
        """
        Liste toutes les permissions.
        """
        permissions = Permission.objects.all()
        return Response(PermissionReadSerializer(permissions, many=True).data)


class UserPasswordMixin:
    @action(
        detail=False,
        methods=['post'],
        url_name='user-forgot-password',
        url_path='forgot-password',
        permission_classes=[AllowAny])
    def forgot_password(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Toujours répondre de manière générique
            return Response({"detail": "If this email exists, a reset link has been sent."})

        # Générer un token unique
        token = secrets.token_urlsafe(32)
        expiry = timezone.now() + timedelta(hours=1)  # valable 1h

        # Stocker le token et sa date d'expiration dans le modèle User ou un modèle dédié
        UserPasswordReset.objects.create(
            user=user,
            token=token,
            expiry=expiry
        )

        # Créer le lien de réinitialisation
        reset_link = f"https://tonfrontend.com/reset-password?token={token}"

        # Envoyer le mail
        subject = "Réinitialisation de votre mot de passe"
        message = f"Bonjour,\n\nPour réinitialiser votre mot de passe, cliquez sur ce lien :\n{reset_link}\n\nCordialement,\nL’équipe."
        send_mail(subject, message, None, [user.email], fail_silently=False)

        return Response({"detail": "If this email exists, a reset link has been sent."})

    @action(
        detail=False,
        methods=['post'],
        url_name='user-reset-password',
        url_path='reset-password',
        permission_classes=[AllowAny])
    def reset_password(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({"detail": "Token and new_password are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_reset = UserPasswordReset.objects.get(token=token)
        except UserPasswordReset.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier expiration
        if user_reset.expiry < timezone.now():
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Modifier le mot de passe
        user = user_reset.user
        user.set_password(new_password)
        user.save()
        # Supprimer le token après utilisation
        user_reset.delete()

        return Response({"detail": "Password reset successful"})

    @action(
        detail=False,
        methods=['post'],
        url_path=r'verify-password-actual/(?P<user_id>[^/.]+)',
        url_name='user-verify-password-actual',
        permission_classes=[IsAuthenticated]
    )
    def verify_password_actual(self, request: Request, pk=None, user_id=None):
        """
        Vérifie que le mot de passe fourni correspond au mot de passe actuel de l'utilisateur.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        password = request.data.get('password')
        result = bool(password and user.check_password(password))
        return Response({"result": result})

    @action(
        detail=False,
        methods=['patch', 'put'],
        url_path=r'modify-password/(?P<user_id>[^/.]+)',
        url_name='user-modify-password',
        permission_classes=[IsAuthenticated]
    )
    def modify_password(self, request: Request, pk=None, user_id=None):
        """
        Modifier le mot de passe d'un utilisateur donné.
        """
        try:
            _user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserPasswordWrite(_user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()

        return Response(UserReadSerializer(user).data)
