from rest_framework import serializers
from workshop.models import (
    Worker, CustomerWorkshop, OrderWorkshop, Workshop,
    OrderWorkshopGroup, OrderWorkshopGroup, Fitting, Setting,
    PackageHistory, Package
)

from django.db import transaction
from django.db.models import Q
from users.serializers import UserWriteSerializer, UserReadSerializer
from django.core.files.uploadedfile import InMemoryUploadedFile
from users.utils import get_or_create_group
from users.models import GROUPS
from django.utils import timezone


class SettingReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = [
            "start_date",
            "end_date",
            "max_workers",
            "max_orders",
            "max_customers",
            "max_fittings",
            "max_order_groups",
            "max_order_ongoing_by_worker",

            "worker_authorization_is_order",
            "worker_authorization_is_fitting",
            "worker_authorization_is_customer",
            "worker_authorization_is_worker",
            "worker_authorization_is_setting",

            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


class PackageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'pk',
            "name",
            "description",
            "features",
            "price",
            "duration",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


class WorkshopReadSerializer(serializers.ModelSerializer):
    settings = SettingReadSerializer()

    class Meta:
        model = Workshop
        fields = [
            "name",
            "slug",
            "description",
            "email",
            "phone",
            "country",
            "city",
            "address",
            "createdAt",
            "settings",
            "updatedAt",
        ]
        read_only_fields = fields


class PackageHistoryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageHistory
        fields = [
            "name",
            "price",
            "start_date",
            "info_paiement",
            "end_date",
            "is_active",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


class WorkerReadSerializer(serializers.ModelSerializer):
    workshop = WorkshopReadSerializer()
    user = UserReadSerializer()
    # methodes fiedls
    total_orders = serializers.SerializerMethodField()
    ongoing_orders = serializers.SerializerMethodField()
    ongoing_orders_by_days = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = [
            "id",
            "user",
            "workshop",
            "is_active",
            "is_owner",
            "is_allowed",
            "start_date",
            "end_date",
            "createdAt",
            "updatedAt",
            "total_orders",
            "ongoing_orders",
            'ongoing_orders_by_days'
        ]
        read_only_fields = fields

    def get_total_orders(self, obj):
        return obj.orders.count()

    def get_ongoing_orders(self, obj):
        # Compte les commandes dont le statut est "IN_PROGRESS" ou "NEW"
        return obj.orders.filter(Q(status="IN_PROGRESS") | Q(status="NEW")).count()

    def get_ongoing_orders_by_days(self, obj):
        orders = obj.orders.filter(Q(status="IN_PROGRESS") | Q(status="NEW"))
        ongoing_orders_by_days = {}
        for order in orders:
            if order.createdAt.date() in ongoing_orders_by_days:
                ongoing_orders_by_days[order.createdAt.strftime(
                    "%d-%b").lower()].append(order.pk)
            else:
                ongoing_orders_by_days[order.createdAt.strftime(
                    "%d-%b").lower()] = [order.pk]
        return ongoing_orders_by_days


class CustomerWorkshopReadSerializer(serializers.ModelSerializer):

    total_orders = serializers.SerializerMethodField()
    ongoing_orders = serializers.SerializerMethodField()
    urgent_orders = serializers.SerializerMethodField()

    class Meta:
        model = CustomerWorkshop
        fields = [
            "id",
            "last_name",
            "first_name",
            "nickname",
            "genre",
            "email",
            "phone",
            "photo",
            "is_active",
            "total_orders",
            "ongoing_orders",
            "urgent_orders",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields

    def get_total_orders(self, obj):
        return obj.orders.count()

    def get_ongoing_orders(self, obj):
        # Compte les commandes dont le statut est "IN_PROGRESS" ou "NEW"
        return obj.orders.filter(Q(status="IN_PROGRESS") | Q(status="NEW")).count()

    def get_urgent_orders(self, obj):
        from django.utils.timezone import now
        from datetime import timedelta
        today_plus_2 = now().date() + timedelta(days=2)
        return obj.orders.filter(
            Q(promised_delivery_date__lte=today_plus_2) | Q(is_urgent=True)
        ).count()


class FittingReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fitting
        fields = [
            "id",
            "fitting_number",
            "scheduled_date",
            "actual_date",
            "notes",
            "adjustments_needed",
            "status",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


class OrderWorkshopReadSerializer(serializers.ModelSerializer):
    worker = WorkerReadSerializer(read_only=True)
    customer = CustomerWorkshopReadSerializer(read_only=True)
    fittings = FittingReadSerializer(many=True, read_only=True)

    class Meta:
        model = OrderWorkshop
        fields = [
            "id",
            "number",
            "worker",
            "customer",
            "gender",
            "type_of_clothing",
            "description",
            "measurement",
            "description_of_fabric",
            "photo_of_fabric",
            "clothing_model",
            "description_of_model",
            "photo_of_clothing_model",
            "amount",
            "down_payment",
            "payment_status",
            "status",
            "is_urgent",
            "assign_date",
            "is_deleted",
            "estimated_delivery_date",
            "promised_delivery_date",
            "actual_delivery_date",
            "createdAt",
            "updatedAt",
            "fittings",
        ]
        read_only_fields = fields


class OrderWorkshopGroupReadSerializer(serializers.ModelSerializer):
    orders = OrderWorkshopReadSerializer(many=True, read_only=True)

    class Meta:
        model = OrderWorkshopGroup
        fields = [
            "id",
            "number",
            "description",
            "orders",
            "total_amount",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = fields


# --- Serializers pour stat_orders_workshop ---

class BarChartItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    Clients = serializers.IntegerField()
    Commandes = serializers.IntegerField()


class LineChartItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    orders = serializers.IntegerField()


class PieChartItemSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.IntegerField()


class StatOrdersWorkshopSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_amount = serializers.FloatField()
    total_paid = serializers.IntegerField()
    total_in_progress = serializers.IntegerField()
    avg_orders_per_client = serializers.FloatField()
    bar_chart = BarChartItemSerializer(many=True)
    line_chart = LineChartItemSerializer(many=True)
    pie_chart = PieChartItemSerializer(many=True)

# --- Serializers pour stat_customers_workshop ---


class StatCustomersWorkshopSerializer(serializers.Serializer):
    total_customers = serializers.IntegerField()
