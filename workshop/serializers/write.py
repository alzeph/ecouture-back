from rest_framework import serializers
from workshop.models import (
    Worker, CustomerWorkshop, OrderWorkshop, Workshop,
    OrderWorkshopGroup, OrderWorkshopGroup, Fitting, Setting,
    PackageHistory
)

from django.db import transaction
from django.db.models import Q
from users.serializers import UserWriteSerializer
from users.utils import get_or_create_group
from users.models import GROUPS


class WorkshopWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workshop
        fields = [
            'name', 'description', 'email', 'phone',
            'country', 'city', 'address', 'slug'
        ] 
        
        extra_kwargs = {
            "name": {"required": False},
            "description": {"required": False},
            "phone": {"required": False},
            "country": {"required": False},
            "city": {"required": False},
            "address": {"required": False},
        }
        read_only_fields = ["slug"]
                

class WorkerWriteSerializer(serializers.ModelSerializer):
    user = UserWriteSerializer(required=False)

    class Meta:
        model = Worker
        fields = [
            "id",
            "user",
            "is_active",
            "is_allowed",
            "start_date",
            "end_date",
            "is_owner",
        ]
        extra_kwargs = {
            "start_date": {"required": False},
            "end_date": {"required": False},
            "is_active": {"required": False},
            "is_allowed": {"required": False},
            "is_owner": {"required": False},
        }
        read_only_fields = ["id"]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user_serializer = UserWriteSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = user_serializer.save()
            worker = Worker.objects.create(user=user, **validated_data)
        user.groups.add(get_or_create_group(GROUPS["WORKERS"]))
        user.save()
        return worker

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user_serializer = UserWriteSerializer(
                instance=instance.user, data=user_data, partial=True
            )
            user_serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                user_serializer.save()
        return super().update(instance, validated_data)


class WorkerWriteForWorkshopSerializer(serializers.ModelSerializer):
    user = UserWriteSerializer(required=False)
    workshop = WorkshopWriteSerializer(required=False)


    class Meta:
        model = Worker
        fields = [
            "id",
            "user",
            "workshop",
            "is_active",
            "is_allowed",
            "start_date",
            "end_date",
            'is_owner',
        ]
        extra_kwargs = {
            "start_date": {"required": False},
            "end_date": {"required": False},
            "is_active": {"required": False},
            "is_allowed": {"required": False},
            "is_owner": {"required": False},
        }
        
    def create(self, validated_data):
        workshop_data = validated_data.pop("workshop")
        workshop_serializer = WorkshopWriteSerializer(data=workshop_data)
        workshop_serializer.is_valid(raise_exception=True)
        user_data = validated_data.pop("user")
        user_serializer = UserWriteSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            workshop = workshop_serializer.save()
            user= user_serializer.save()
            worker = Worker.objects.create(workshop=workshop, user=user, **validated_data)
        return worker


class CustomerWorkshopWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerWorkshop
        fields = [
            "last_name",
            "first_name",
            "nickname",
            "genre",
            "email",
            "phone",
            "photo",
        ]
        extra_kwargs = {
            "last_name": {"required": False},
            "first_name": {"required": False},
            "nickname": {"required": False},
            "genre": {"required": False},
            "email": {"required": False},
            "phone": {"required": False},
            "photo": {"required": False},
        }

class OrderWorkshopWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderWorkshop
        fields = [
            "customer",
            "worker",
            "gender",
            "type_of_clothing",
            "measurement",
            "description",
            "description_of_fabric",
            "photo_of_fabric",
            "clothing_model",
            "description_of_model",
            "photo_of_clothing_model",
            "amount",
            "down_payment",
            "status",
            "estimated_delivery_date",
            "promised_delivery_date",
            "actual_delivery_date",
            "is_urgent",
        ]
        extra_kwargs = {
            "customer": {"required": False},
            "worker": {"required": False},
            "gender": {"required": False},
            "type_of_clothing": {"required": False},
            "measurement": {"required": False},
            "description_of_fabric": {"required": False},
            "photo_of_fabric": {"required": False},
            "clothing_model": {"required": False},
            "description_of_model": {"required": False},
            "photo_of_clothing_model": {"required": False},
            "amount": {"required": False},
            "down_payment": {"required": False},
            "status": {"required": False},
            "estimated_delivery_date": {"required": False},
            "promised_delivery_date": {"required": False},
            "actual_delivery_date": {"required": False},
            "is_urgent": {"required": False},
        }

    def create(self, validated_data):
        return OrderWorkshop.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class FittingWriteSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(
        queryset=OrderWorkshop.objects.all())

    class Meta:
        model = Fitting
        fields = [
            "order",
            "scheduled_date",
            "actual_date",
            "notes",
            "adjustments_needed",
            "status",
        ]
        extra_kwargs = {
            "order": {"required": False},
            "scheduled_date": {"required": False},
            "actual_date": {"required": False},
            "notes": {"required": False},
            "adjustments_needed": {"required": False},
            "status": {"required": False},
        }
        read_only_fields = ["fitting_number", "createdAt", "updatedAt"]

    def create(self, validated_data):
        # fitting_number est automatiquement attribué dans le modèle
        return Fitting.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # mise à jour partielle possible
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class OrderWorkshopGroupWriteSerializer(serializers.ModelSerializer):
    orders = serializers.PrimaryKeyRelatedField(
        queryset=OrderWorkshop.objects.all(),
        many=True,
        required=True
    )

    class Meta:
        model = OrderWorkshopGroup
        fields = [
            "description",
            "orders",
        ]
        extra_kwargs = {
            "description": {"required": False},
            "orders": {"required": False},
        }

    def create(self, validated_data):
        orders_data = validated_data.pop("orders", [])
        group = OrderWorkshopGroup.objects.create(**validated_data)
        group.orders.set(orders_data)
        return group

    def update(self, instance, validated_data):
        orders_data = validated_data.pop("orders", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if orders_data is not None:
            instance.orders.set(orders_data)
        return instance

class SettingWriteSerializer(serializers.ModelSerializer):
    worker_authorization_is_order = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), many=True, required=False
    )
    worker_authorization_is_fitting = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), many=True, required=False
    )
    worker_authorization_is_customer = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), many=True, required=False
    )
    worker_authorization_is_worker = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), many=True, required=False
    )
    worker_authorization_is_setting = serializers.PrimaryKeyRelatedField(
        queryset=Worker.objects.all(), many=True, required=False
    )

    class Meta:
        model = Setting
        fields = [
            "start_date",
            "end_date",

            "worker_authorization_is_order",
            "worker_authorization_is_fitting",
            "worker_authorization_is_customer",
            "worker_authorization_is_worker",
            "worker_authorization_is_setting",
        ]
        extra_kwargs = {
            "worker_authorization_is_order": {"required": False},
            "worker_authorization_is_fitting": {"required": False},
            "worker_authorization_is_customer": {"required": False},
            "worker_authorization_is_worker": {"required": False},
            "worker_authorization_is_setting": {"required": False},
            
            "max_workers" : {"required": False},
            "max_orders" : {"required": False},
            "max_customers" : {"required": False},
            "max_fittings" : {"required": False},
            "max_order_groups" : {"required": False},
            "max_order_ongoing_by_worker" : {"required": False},
        }
        read_only_fields = ["start_date", "end_date"]

    def create(self, validated_data):
        workers_data = {key: validated_data.pop(key, []) for key in [
            "worker_authorization_is_order",
            "worker_authorization_is_fitting",
            "worker_authorization_is_customer",
            "worker_authorization_is_worker",
            "worker_authorization_is_setting"
        ]}
        setting = Setting.objects.create(**validated_data)
        for key, workers in workers_data.items():
            getattr(setting, key).set(workers)
        return setting

    def update(self, instance, validated_data):
        workers_data = {key: validated_data.pop(key, None) for key in [
            "worker_authorization_is_order",
            "worker_authorization_is_fitting",
            "worker_authorization_is_customer",
            "worker_authorization_is_worker",
            "worker_authorization_is_setting"
        ]}
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        for key, workers in workers_data.items():
            if workers is not None:
                getattr(instance, key).set(workers)
        return instance

class PackageHistoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageHistory
        fields = [
            "workshop",
            "name",
            "price",
            "info_paiement",
        ]

