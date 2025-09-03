from ecouture.serializers import (
    NotFound404ResponseSerializer, ValidationError400Serializer,
    ValidationError400Serializer, VerifyFieldSerializer, ExistsResponseSerializer,
    WorkerAuthorisationSerializer
)

from django.db.models import Sum
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from workshop.models import (
    Worker, CustomerWorkshop, OrderWorkshop, Workshop,
    OrderWorkshopGroup, OrderWorkshopGroup, Fitting, Setting,
    PackageHistory
)

from workshop.serializers.read import (
    PackageReadSerializer, PackageHistoryReadSerializer,
    WorkerReadSerializer, CustomerWorkshopReadSerializer, FittingReadSerializer,
    OrderWorkshopReadSerializer, OrderWorkshopGroupReadSerializer, SettingReadSerializer,
    StatOrdersWorkshopSerializer, StatCustomersWorkshopSerializer
)

from workshop.serializers.write import (
    WorkerWriteSerializer,
    CustomerWorkshopWriteSerializer, OrderWorkshopWriteSerializer, FittingWriteSerializer,
    OrderWorkshopGroupWriteSerializer, SettingWriteSerializer, PackageHistoryWriteSerializer
)

from datetime import datetime, timedelta
from django.db.models import Count, Sum
from collections import defaultdict
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from workshop.filters import WorkerFilterSet, CustomerWorkshopFilterSet, OrderWorkshopFilterSet

from django.contrib.auth import get_user_model
User = get_user_model()


class WorkerMixin:
    """
    Mixin to provide worker-related functionality.
    """

    @extend_schema(
        methods=["get"],
        summary="Récupérer les workers",
        description="Retourne la liste paginée des workers d’un atelier.",
        responses={
            200: WorkerReadSerializer(many=True),
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer,
        },
        parameters=[
            # Pagination
            OpenApiParameter(
                name="page",
                type=int,
                description="Numéro de la page à récupérer"
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                description="Nombre de résultats par page"
            ),

            # Filtres Worker
            OpenApiParameter(
                name="is_active",
                type=bool,
                description="Filtrer sur l’état actif du worker"
            ),
            OpenApiParameter(
                name="is_allowed",
                type=bool,
                description="Filtrer sur l’autorisation du worker"
            ),
        ]
    )
    @extend_schema(
        methods=["post"],
        summary="Créer un worker",
        description="Crée un nouveau worker dans l’atelier.",
        request=WorkerWriteSerializer,
        responses={
            201: WorkerReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        },
    )
    @action(
        detail=True,
        methods=['get', 'post'],
        url_path='users/workers',
        url_name=r'workers-list',
        permission_classes=[IsAuthenticated]
    )
    def worker_list(self, request: Request, pk=None):
        workshop = self.get_object()

        if request.method == 'GET':
            queryset = workshop.workers.all().order_by(
                'user__last_name', 'user__first_name')
            filtered_qs = WorkerFilterSet(request.GET, queryset=queryset).qs

            page = self.paginate_queryset(filtered_qs)
            serializer = WorkerReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WorkerWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            worker = serializer.save(workshop=workshop)
        return Response(
            WorkerReadSerializer(worker).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        methods=['get'],
        summary="recuperer un worker",
        description="permet de recuperer un worker",
        responses={
            200: WorkerReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="mettre a jour un worker",
        description="permet de mettre a jour un worker",
        request=WorkerWriteSerializer,
        responses={
            200: WorkerReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="supprimer un worker",
        description="permet de supprimer un worker",
        responses={
            204: None,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['patch', 'delete', 'get'],
        url_path=r'users/workers/(?P<worker_pk>[^/.]+)',
        url_name='workers-detail',
        permission_classes=[IsAuthenticated]
    )
    def worker_detail(self, request: Request, pk=None, worker_pk=None):
        workshop = self.get_object()

        try:
            _worker: Worker = workshop.workers.get(pk=worker_pk)
            if request.method == 'GET':
                return Response(WorkerReadSerializer(_worker).data)

            if request.method == 'PATCH':

                serializer = WorkerWriteSerializer(
                    _worker, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                with transaction.atomic():
                    worker = serializer.save()
                return Response(WorkerReadSerializer(worker).data)
            # methods delete
            _worker.is_active = False
            _worker
            _worker.save(update_fields=['is_active'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(e)
            return Response({"detail": f"Worker not found {e}"},
                            status=status.HTTP_404_NOT_FOUND)


class CustomerWorkshopMixin:
    """
    Mixin to provide customer workshop-related functionality.
    """
    @extend_schema(
        methods=['get'],
        summary="recuperer la liste des clients de l'atelier",
        description="permet de recuperer la liste des clients de l'atelier",
        responses={
            200: CustomerWorkshopReadSerializer(many=True),
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        },
        parameters=[
            # paramètres de pagination
            OpenApiParameter(
                name="page",
                type=int,
                description="Numéro de la page à récupérer"
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                description="Nombre de résultats par page"
            ),
            # paramètres du FilterSet
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                many=True,  # 👈 indique que ce paramètre peut être multiple
                description=(
                    "Filtrer par plusieurs noms (last_name, first_name ou nickname). "
                    "Exemple : ?name=cedric&name=paul"
                ),
            ),
            OpenApiParameter(
                name="genre",
                type=str,
                description="Filtrer par genre"
            ),
            OpenApiParameter(
                name="is_active",
                type=bool,
                description="Filtrer si le client est actif ou non"
            ),
        ]
    )
    @extend_schema(
        methods=['post'],
        summary="créer un client de l'atelier",
        description="permet de créer un client de l'atelier",
        request=CustomerWorkshopWriteSerializer,
        responses={
            200: CustomerWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }

    )
    @action(
        detail=True,
        methods=['get', 'post'],
        url_path=r'customers-workshops',
        url_name='customers-list',
        permission_classes=[IsAuthenticated]
    )
    def customer_workshop(self, request: Request, pk=None):
        workshop = self.get_object()

        from django.utils import timezone

        if request.method == 'GET':
            queryset = workshop.customers.filter(
                is_active=True).order_by('-createdAt')
            filtered_qs = CustomerWorkshopFilterSet(
                request.GET, queryset=queryset).qs

            page = self.paginate_queryset(filtered_qs)
            serializer = CustomerWorkshopReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # creation (POST)
        try:
            serializer = CustomerWorkshopWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                customer = serializer.save(workshop=workshop)
        except ValidationError as e:
            return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(
            CustomerWorkshopReadSerializer(customer).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        methods=['get'],
        summary="recuperer un client",
        description="permet de recuperer un client",
        responses={
            200: CustomerWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="mettre a jour un client",
        description="permet de mettre a jour un client",
        request=CustomerWorkshopWriteSerializer,
        responses={
            200: CustomerWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="supprimer un client",
        description="permet de supprimer un client",
        responses={
            204: None,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['patch', 'delete', 'get'],
        url_path=r'customers-workshops/(?P<customer_pk>[^/.]+)',
        url_name='customers-detail',
        permission_classes=[IsAuthenticated]
    )
    def customer_workshop_detail(self, request: Request, pk=None, customer_pk=None):
        workshop = self.get_object()

        try:
            _customer: CustomerWorkshop = workshop.customers.get(
                pk=customer_pk)
        except:
            return Response({"detail": "CustomerWorkshop not found"},
                            status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response(CustomerWorkshopReadSerializer(_customer).data)
        if request.method == 'PATCH':
            serializer = CustomerWorkshopWriteSerializer(
                _customer, data=request.data, partial=True)

            # serializer.is_valid()
            # print(request.data)
            # print(serializer.error_messages)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                customer = serializer.save()
            return Response(CustomerWorkshopReadSerializer(customer).data)

        _customer.is_active = False
        _customer.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=['post'],
        summary="verifier le numero de telephone d'un client existe ou non",
        description="permet de verifier le numero de telephone d'un client existe ou non",
        request=VerifyFieldSerializer,
        responses={
            200: ExistsResponseSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path='customers/verify-numbers',
        permission_classes=[IsAuthenticated]
    )
    def customer_workshop_verify_number(self, request: Request, pk=None):
        workshop = self.get_object()

        exclude_phone = request.query_params.get('phone')
        verify_phone = request.data.get('verify_phone')
        if not verify_phone:
            return Response({"detail": f"{verify_phone} is required"}, status=status.HTTP_400_BAD_REQUEST)

        customer_qs = workshop.customers.all()
        if exclude_phone:
            customer_qs = customer_qs.exclude(phone=exclude_phone)

        exists = customer_qs.filter(phone=verify_phone).exists()
        return Response({"exists": exists})


class OrderWorkshopMixin:

    """
    Mixin to provide order workshop-related functionality.
    """

    @extend_schema(
        methods=['get'],
        summary="recuperer la liste des commandes",
        description="permet de recuperer la liste des commandes",
        responses={
            200: OrderWorkshopReadSerializer(many=True),
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        },
        parameters=[
            # Pagination
            OpenApiParameter(
                name="page",
                type=int,
                description="Numéro de la page à récupérer"
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                description="Nombre de résultats par page"
            ),

            # Filtres par choix
            OpenApiParameter(
                name="gender",
                type=str,
                description="Genre du client (choices: {})".format(
                    ", ".join([c[0] for c in OrderWorkshop.Gender.choices])
                ),
            ),
            OpenApiParameter(
                name="type_of_clothing",
                type=str,
                description="Type de vêtement (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.TypeOfClothing.choices])
                ),
            ),
            OpenApiParameter(
                name="payment_status",
                type=str,
                description="Statut du paiement (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.PaymentStatus.choices])
                ),
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                style="form",
                explode=True,  # permet de passer plusieurs fois le param
                required=False,

                enum=[c[0] for c in OrderWorkshop.OrderStatus.choices],
                description="Statut de la commande (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.OrderStatus.choices])
                ),
            ),

            # Filtres FK
            OpenApiParameter(
                name="customer",
                type=OpenApiTypes.NUMBER,
                many=True,  # 👈 indique que ce paramètre peut être multiple
                description=(
                    "Filtrer par plusieurs noms (last_name, first_name ou nickname). "
                    "Exemple : ?name=cedric&name=paul"
                ),
            ),
            OpenApiParameter(
                name="worker",
                type=OpenApiTypes.NUMBER,
                many=True,  # 👈 indique que ce paramètre peut être multiple
                description=(
                    "Filtrer par plusieurs noms (last_name, first_name ou nickname). "
                    "Exemple : ?name=cedric&name=paul"
                )
            ),

            # Booléen
            OpenApiParameter(
                name="is_urgent",
                type=bool,
                description="Filtrer les commandes urgentes"
            ),

            # Filtres sur période de création
            OpenApiParameter(
                name="created_after",
                type=str,
                description="Commandes créées après cette date"
            ),
            OpenApiParameter(
                name="created_before",
                type=str,
                description="Commandes créées avant cette date"
            ),
            
             # Filtres sur la date de livraison
            OpenApiParameter(
                name="delivery_after",
                type=str,
                description="Commandes les commande a livrer après cette date"
            ),
            OpenApiParameter(
                name="delivery_before",
                type=str,
                description="Commandes a liver avant cette date"
            ),

            # Recherche textuelle
            OpenApiParameter(
                name="q",
                type=str,
                description="Recherche libre (descriptions, tissus, modèle)"
            ),
        ]
    )
    @extend_schema(
        methods=['post'],
        summary="creer une commande",
        description="permet de créer une commande",
        request=OrderWorkshopWriteSerializer,
        responses={
            201: OrderWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get', 'post'],
        url_path=r"orders",
        url_name="orders-list",
        permission_classes=[IsAuthenticated]
    )
    def order_workshop(self, request: Request, pk=None):
        workshop = self.get_object()
        if request.method == 'GET':
            queryset = OrderWorkshop.objects.filter(customer__workshop=workshop, is_deleted=False).order_by(
                'promised_delivery_date')
         
            filtered_qs = OrderWorkshopFilterSet(
                request.GET, queryset=queryset).qs

            page = self.paginate_queryset(filtered_qs)
            serializer = OrderWorkshopReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = OrderWorkshopWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            orderWorkshop = serializer.save()
        return Response(OrderWorkshopReadSerializer(orderWorkshop).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['get'],
        summary="recuperer une commande",
        description="permet de recuperer une commande",
        responses={
            200: OrderWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="mettre a jour une commande",
        description="permet de mettre a jour une commande",
        request=OrderWorkshopWriteSerializer,
        responses={
            200: OrderWorkshopReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="supprimer une commande",
        description="permet de supprimer une commande",
        responses={
            204: None,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=["patch", "delete", 'get'],
        url_path=r"orders/(?P<order_pk>\d+)",
        url_name="orders-detail",
        permission_classes=[IsAuthenticated]
    )
    def order_workshop_detail(self, request: Request, pk=None, order_pk=None):
        workshop = self.get_object()

        try:
            order = OrderWorkshop.objects.get(pk=order_pk)
        except OrderWorkshop.DoesNotExist:
            return Response({"detail": "Order not found for this customer in this workshop."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response(OrderWorkshopReadSerializer(order).data)

        if request.method == "PATCH" or request.method == 'PUT':
            serializer = OrderWorkshopWriteSerializer(
                order, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                order = serializer.save()
                # print(OrderWorkshopReadSerializer(order).data)
            return Response(OrderWorkshopReadSerializer(order).data)

        # DELETE
        order.is_deleted = True
        order.save(update_fields=['is_deleted'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderWorkshopGroupMixin:

    @extend_schema(
        methods=['get'],
        summary="recuperer la liste des groupes de commandes",
        description="permet de recuperer la liste des groupes de commandes",
        responses={
            200: OrderWorkshopGroupReadSerializer(many=True),
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['post'],
        summary="creer un groupe de commandes",
        description="permet de créer un groupe de commandes",
        request=OrderWorkshopGroupWriteSerializer,
        responses={
            201: OrderWorkshopGroupReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get', 'post'],
        url_path=r"orders/groups",
        url_name="order-groups-list"
    )
    def order_workshop_group(self, request: Request, pk=None):
        workshop = self.get_object()

        if request.method == "GET":
            queryset = OrderWorkshopGroup.objects.filter(
                orders__customer__workshop=workshop
            ).distinct().order_by('-createdAt')

            page = self.paginate_queryset(queryset)
            serializer = OrderWorkshopGroupReadSerializer(
                page, many=True)
            return self.get_paginated_response(serializer.data)

        # Création POST
        serializer = OrderWorkshopGroupWriteSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            order_group = serializer.save()
        return Response(OrderWorkshopGroupReadSerializer(order_group).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['get'],
        summary="recuperer un groupe de commandes",
        description="permet de recuperer un groupe de commandes",
        responses={
            200: OrderWorkshopGroupReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="mettre a jour un groupe de commandes",
        description="permet de mettre a jour un groupe de commandes",
        request=OrderWorkshopGroupWriteSerializer,
        responses={
            200: OrderWorkshopGroupReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="supprimer un groupe de commandes",
        description="permet de supprimer un groupe de commandes",
        responses={
            204: None,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=["patch", "delete", 'get'],
        url_path=r"orders/groups/(?P<order_group_pk>\d+)",
        url_name="order-groups-detail"
    )
    def order_workshop_group_detail(self, request: Request, pk=None, order_group_pk=None):
        workshop = self.get_object()

        try:
            order_group = OrderWorkshopGroup.objects.get(pk=order_group_pk)
        except OrderWorkshopGroup.DoesNotExist:
            return Response({"detail": "Order group not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response(OrderWorkshopGroupReadSerializer(order_group).data)

        if request.method == "PATCH" or request.method == 'PUT':
            serializer = OrderWorkshopGroupWriteSerializer(
                order_group, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            order_group = serializer.save()
            return Response(OrderWorkshopGroupReadSerializer(order_group).data)

        # DELETE
        order_group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FittingMixin:

    @extend_schema(
        methods=['post'],
        summary="Créer un fitting",
        description="Crée un nouveau fitting dans l’atelier.",
        request=FittingWriteSerializer,
        responses={
            201: FittingReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="fittings",
        url_name="fittings-list"
    )
    def fitting(self, request: Request, pk=None):
        workshop = self.get_object()

        # Création POST
        serializer = FittingWriteSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            fitting = serializer.save()
        return Response(FittingReadSerializer(fitting).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['patch'],
        summary="Modifier un fitting",
        description="Modifie un fitting dans l’atelier.",
        request=FittingWriteSerializer,
        responses={
            200: FittingReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="Supprimer un fitting",
        description="Supprime un fitting dans l’atelier.",
        responses={
            204: None,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"orders/fittings/(?P<fitting_pk>\d+)",
        url_name="fittings-detail"
    )
    def fitting_detail(self, request: Request, pk=None, fitting_pk=None):

        workshop = self.get_object()

        try:
            _fitting = Fitting.objects.get(pk=fitting_pk)
        except Fitting.DoesNotExist:
            return Response({"detail": "Fittin group not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.method != "DELETE":
            serializer = FittingWriteSerializer(
                _fitting, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            fitting = serializer.save()
            return Response(FittingReadSerializer(fitting).data)

        # DELETE
        _fitting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SettingMixin:

    @extend_schema(
        methods=['patch'],
        summary="Modifier un setting",
        description="Modifie un setting dans l’atelier.",
        request=SettingWriteSerializer,
        responses={
            200: SettingReadSerializer,
            400: ValidationError400Serializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['patch'],
        url_path='setting',
        url_name='settings-detail',
        permission_classes=[IsAuthenticated])
    def settings_detail(self, request: Request, pk=None):
        worshop = self.get_object()
        try:
            setting: Setting = worshop.settings
        except Setting.DoesNotExist:
            return Response({"detail": "Setting not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = SettingWriteSerializer(
            setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            setting = serializer.save(worshop=worshop)
        return Response(SettingReadSerializer(setting).data)

    @extend_schema(
        methods=['get'],
        summary="Voir si il le quota de tralleurs est atteint",
        description="Voir si il le quota de tralleurs est atteint",
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='setting/workers/authorised',
        url_name='settings-worker-count-authorised',
        permission_classes=[IsAuthenticated])
    def worker_authorised_is_create(self, request: Request, pk=None):
        """
        Check if the number of workers in the workshop is less than the maximum allowed in the Setting.
        Used to check if the user is allowed to create a new worker.
        """
        workshop = self.get_object()
        setting: Setting = workshop.settings
        elt_count = workshop.workers.count()
        return Response({"exists": elt_count < setting.max_workers})

    @extend_schema(
        methods=['get'],
        summary="Voir si il le quota de clients est atteint",
        description="Voir si il le quota de clients est atteint",
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='setting/customers/authorised',
        url_name='settings-customer-count-authorised',
        permission_classes=[IsAuthenticated])
    def customer_authorised_is_create(self, request: Request, pk=None):
        """
        Check if the number of customers in the workshop is less than the maximum allowed in the Setting.
        Used to verify if a new customer can be created in the workshop.
        """

        workshop = self.get_object()
        setting: Setting = workshop.settings
        elt_count = workshop.customers.count()
        return Response({"exists": elt_count < setting.max_customers})

    @extend_schema(
        methods=['get'],
        summary="Voir si il le quota de commandes est atteint",
        description="Voir si il le quota de commandes est atteint",
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='setting/orders/authorised',
        url_name='settings-order-count-authorised',
        permission_classes=[IsAuthenticated])
    def order_authorised_is_create(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        elt_count = CustomerWorkshop.objects.filter(
            workshop=workshop).count()
        return Response({"exists": elt_count < setting.max_orders})

    @extend_schema(
        methods=['get'],
        summary="Voir si il le quota de ajustements est atteint",
        description="Voir si il le quota de ajustements est atteint",
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get'],
        url_path='setting/fittings/authorised',
        url_name='settings-fitting-count-authorised',
        permission_classes=[IsAuthenticated])
    def fitting_authorised_is_create(self, request: Request, pk=None):
        """
        Check if the number of fittings in the workshop is less than the maximum allowed in the Setting.
        Used to check if the user is allowed to create a new fitting.
        """
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        elt_count = Fitting.objects.filter(
            order__worker__workshop=workshop).count()
        return Response({"exists": elt_count < setting.max_orders})

    @extend_schema(
        methods=['post'],
        summary="Voir si le tralleur est autorisé à créer une commande",
        description="Voir si le tralleur est autorisé à créer une commande",
        request=WorkerAuthorisationSerializer,
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'settings/orders/worker-authorised',
        url_name='settings-order-authorised',
        permission_classes=[IsAuthenticated]
    )
    def worker_is_authorisation_is_order(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        worker_pk = request.data['worker_pk']
        try:
            setting.worker_authorization_is_order.get(pk=worker_pk)
            return Response({'exists': True})
        except Worker.DoesNotExist:
            return Response({'exists': False})

    @extend_schema(
        methods=['post'],
        summary="Voir si le tralleur est autorisé à créer un client",
        description="Voir si le tralleur est autorisé à créer un client",
        request=WorkerAuthorisationSerializer,
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'settings/customers/worker-authorised',
        url_name='settings-customer-authorised',
        permission_classes=[IsAuthenticated]
    )
    def worker_is_authorisation_is_customer(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        worker_pk = request.data['worker_pk']
        try:
            setting.worker_authorization_is_customer.get(pk=worker_pk)
            return Response({'exists': True})
        except Setting.DoesNotExist:
            return Response({'exists': False})

    @extend_schema(
        methods=['post'],
        summary="Voir si le tralleur est autorisé à créer un ajustement",
        description="Voir si le tralleur est autorisé à créer un ajustement",
        request=WorkerAuthorisationSerializer,
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'settings/fittings/worker-authorised',
        url_name='settings-fitting-authorised',
        permission_classes=[IsAuthenticated]
    )
    def worker_is_authorisation_is_fitings(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        worker_pk = request.data['worker_pk']
        try:
            setting.worker_authorization_is_fitting.get(pk=worker_pk)
            return Response({'exists': True})
        except Setting.DoesNotExist:
            return Response({'exists': False})

    @extend_schema(
        methods=['post'],
        summary="Voir si le tralleur est autorisé à créer un ajustement",
        description="Voir si le tralleur est autorisé à créer un ajustement",
        request=WorkerAuthorisationSerializer,
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'settings/workers/worker-authorised',
        url_name='settings-worker-authorised',
        permission_classes=[IsAuthenticated]
    )
    def worker_is_authorisation_is_worker(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        worker_pk = request.data['worker_pk']
        try:
            setting.worker_authorization_is_worker.get(pk=worker_pk)
            return Response({'exists': True})
        except Setting.DoesNotExist:
            return Response({'exists': False})

    @extend_schema(
        methods=['post'],
        summary="Voir si le tralleur est autorisé à créer un ajustement",
        description="Voir si le tralleur est autorisé à créer un ajustement",
        request=WorkerAuthorisationSerializer,
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'settings/settings/worker-authorised',
        url_name='settings-setting-authorised',
        permission_classes=[IsAuthenticated]
    )
    def worker_is_authorisation_is_setting(self, request: Request, pk=None):
        workshop: Workshop = self.get_object()
        setting: Setting = workshop.settings
        worker_pk = request.data['worker_pk']
        try:
            setting.worker_authorization_is_setting.get(pk=worker_pk)
            return Response({'exists': True})
        except Setting.DoesNotExist:
            return Response({'exists': False})


class PackageHistoryMixin:

    @extend_schema(
        methods=['post'],
        summary="payer un nouvelle abonnement",
        description="Permet de payer un nouvelle abonnement",
        responses={
            200: PackageHistoryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['get'],
        summary="recupere hytorique des abonnements",
        description="Permet de recupere la lsite de tout les abonnements",
        responses={
            200: PackageHistoryReadSerializer(many=True),
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=True,
        methods=['get', 'post'],
        url_path='package-history',
        url_name='package-histories-list',
        permission_classes=[IsAuthenticated]
    )
    def package_hitories_list(self, request: Request, pk=None):
        """
        Check if the user is authorised to access package history.
        """
        if request.method == 'GET':
            workshop = self.get_object()
            packages = workshop.package_histories.all().order_by('-createdAt')
            page = self.paginate_queryset(packages)
            return self.get_paginated_response(PackageHistoryReadSerializer(page, many=True).data)

        serializer = PackageHistoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            package_history = serializer.save()
        return Response(PackageHistoryReadSerializer(package_history).data, status=status.HTTP_201_CREATED)


class StatMixin:
    """Mixin regroupant les statistiques liées aux ateliers (workshop)."""

    def _get_date_range(self, request):
        """Récupère ou calcule la période de stats (par défaut : 7 derniers jours)."""
        today = datetime.now()

        created_after = request.query_params.get("created_after")
        created_before = request.query_params.get("created_before")

        if created_after and created_before:
            try:
                start_date = datetime.fromisoformat(created_after)
                end_date = datetime.fromisoformat(created_before)
            except ValueError:
                start_date = today - timedelta(days=6)
                end_date = today
        else:
            start_date = today - timedelta(days=6)
            end_date = today

        return start_date, end_date

    @extend_schema(
        methods=['get'],
        summary="Statistiques sur les commandes",
        description="Statistiques sur les commandes",
        responses={
            200: StatOrdersWorkshopSerializer,
            404: NotFound404ResponseSerializer
        },
        parameters=[
            # Pagination
            OpenApiParameter(
                name="page",
                type=int,
                description="Numéro de la page à récupérer"
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                description="Nombre de résultats par page"
            ),

            # Filtres par choix
            OpenApiParameter(
                name="gender",
                type=str,
                description="Genre du client (choices: {})".format(
                    ", ".join([c[0] for c in OrderWorkshop.Gender.choices])
                ),
            ),
            OpenApiParameter(
                name="type_of_clothing",
                type=str,
                description="Type de vêtement (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.TypeOfClothing.choices])
                ),
            ),
            OpenApiParameter(
                name="payment_status",
                type=str,
                description="Statut du paiement (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.PaymentStatus.choices])
                ),
            ),
            OpenApiParameter(
                name="status",
                type=str,
                description="Statut de la commande (choices: {})".format(
                    ", ".join([c[0]
                              for c in OrderWorkshop.OrderStatus.choices])
                ),
            ),

            # Filtres FK
            OpenApiParameter(
                name="customer",
                type=int,
                description="ID du client"
            ),
            OpenApiParameter(
                name="worker",
                type=int,
                description="ID du tailleur/ouvrier"
            ),

            # Booléen
            OpenApiParameter(
                name="is_urgent",
                type=bool,
                description="Filtrer les commandes urgentes"
            ),

            # Filtres sur période de création
            OpenApiParameter(
                name="created_after",
                type=str,
                description="Commandes créées après cette date"
            ),
            OpenApiParameter(
                name="created_before",
                type=str,
                description="Commandes créées avant cette date"
            ),

            # Recherche textuelle
            OpenApiParameter(
                name="q",
                type=str,
                description="Recherche libre (descriptions, tissus, modèle)"
            ),
        ]

    )
    @action(
        detail=True,
        methods=['get'],
        url_path='stats/orders',
        url_name='stats-orders')
    def stat_orders_workshop(self, request, pk=None):
        workshop = self.get_object()
        start_date, end_date = self._get_date_range(request)

        queryset = OrderWorkshop.objects.filter(
            customer__workshop=workshop,
            createdAt__range=(start_date, end_date)
        ).order_by("createdAt")

        filtered_qs = OrderWorkshopFilterSet(request.GET, queryset=queryset).qs

        # Calculs globaux
        total_orders = filtered_qs.count()
        total_amount = filtered_qs.aggregate(total=Sum("amount"))["total"] or 0
        total_paid = filtered_qs.filter(payment_status="PAID").count()
        total_in_progress = filtered_qs.filter(status="IN_PROGRESS").count()

        # Préparation données graphiques
        bar_data = defaultdict(lambda: {"Clients": set(), "Commandes": 0})
        line_data = defaultdict(lambda: {"orders": 0})
        gender_data = defaultdict(int)

        unique_clients = filtered_qs.values_list(
            "customer_id", flat=True).distinct()
        total_clients = unique_clients.count() or 1  # éviter division par 0
        avg_orders_per_client = round(total_orders / total_clients, 2)

        for order in filtered_qs:
            date_str = order.createdAt.strftime("%d-%b").lower()
            bar_data[date_str]["Clients"].add(order.customer_id)
            bar_data[date_str]["Commandes"] += 1
            line_data[date_str]["orders"] += 1
            gender_data[getattr(order, "gender", "Inconnu")] += 1

        # Transformation des sets → int
        bar_chart = [
            {"date": k, "Clients": len(
                v["Clients"]), "Commandes": v["Commandes"]}
            for k, v in sorted(bar_data.items())
        ]
        line_chart = [{"date": k, **v} for k, v in sorted(line_data.items())]
        pie_chart = [{"name": k, "value": v} for k, v in gender_data.items()]

        return Response({
            "total_orders": total_orders,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_in_progress": total_in_progress,
            "avg_orders_per_client": avg_orders_per_client,
            "bar_chart": bar_chart,
            "line_chart": line_chart,
            "pie_chart": pie_chart,
        })

    @extend_schema(
        methods=['get'],
        summary="Statistiques sur les clients",
        description="Statistiques sur les clients",
        responses={
            200: StatCustomersWorkshopSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(detail=True, methods=['get'], url_path='stats/customers', url_name='stats-customers')
    def stat_customers_workshop(self, request, pk=None):
        workshop = self.get_object()
        start_date, end_date = self._get_date_range(request)

        queryset = CustomerWorkshop.objects.filter(
            workshop=workshop,
            createdAt__range=(start_date, end_date)
        )
        filtered_qs = CustomerWorkshopFilterSet(
            request.GET, queryset=queryset).qs

        total_customers = filtered_qs.count()

        return Response({
            "total_customers": total_customers
        })
