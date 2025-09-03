from rest_framework.viewsets import ModelViewSet
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from workshop.mixins import (
    WorkerMixin, FittingMixin, OrderWorkshopMixin,
    CustomerWorkshopMixin, OrderWorkshopGroupMixin, SettingMixin, StatMixin, PackageHistoryMixin
)

from workshop.models import Workshop, Package
from workshop.serializers.read import WorkshopReadSerializer, PackageReadSerializer
from workshop.serializers.write import WorkerWriteForWorkshopSerializer, WorkshopWriteSerializer
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, OpenApiResponse


from ecouture.serializers import (
    VerifyFieldSerializer,
    ExistsResponseSerializer,
    ValidationError400Serializer
)


@method_decorator(csrf_exempt, name='dispatch')
class WorkshopViewSet(
        WorkerMixin,
        CustomerWorkshopMixin,
        OrderWorkshopMixin,
        OrderWorkshopGroupMixin,
        FittingMixin,
        SettingMixin,
        StatMixin,
        PackageHistoryMixin,
        ModelViewSet):
    """
    ViewSet for managing workshops.
    """
    model = Workshop.objects.all()
    queryset = Workshop.objects.all()

    def get_serializer_class(self):
        if self.action in ['create']:
            return WorkerWriteForWorkshopSerializer
        if self.action in ['update', 'partial_update']:
            return WorkshopWriteSerializer
        return WorkshopReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        elif self.action in {"retrieve", "update", "partial_update", "destroy"}:
            return [IsAuthenticated()]
        return super().get_permissions()

    @extend_schema(
        summary="Vérifie si un email existe",
        description="Permet de vérifier si un email est déjà utilisé. Possibilité d'exclure un email existant.",
        request=VerifyFieldSerializer,
        responses={
            200: ExistsResponseSerializer,
            400: ValidationError400Serializer,
        }
    )
    @action(
        detail=False,
        methods=['post'],
        url_path=r"validators-names-unique",
        url_name="name-unique",
        permission_classes=[AllowAny]
    )
    def workshop_validators_names_unique(self, request: Request, pk=None):
        verify_name = request.data.get('verify', None)
        exclude_name = request.data.get('exclude', None)
        if not verify_name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        workshop = Workshop.objects.all()
        if exclude_name:
            workshop = workshop.exclude(name=exclude_name)
        exists = workshop.filter(name=verify_name).exists()
        return Response({"exists": exists})

    @extend_schema(
        summary="Liste des package",
        description="Permet de recupere la liste des package disponibles",
        responses=PackageReadSerializer(many=True),
        filters=False,
    )
    @action(
        detail=False,
        methods=['get'],
        url_path=r"package-list",
        url_name="packages-list",
        permission_classes=[AllowAny],
    )
    def package(self, request: Request, pk=None):
        package = Package.objects.all()
        page = self.paginate_queryset(package)
        serializer = PackageReadSerializer(package, many=True)
        return self.get_paginated_response(serializer.data)
