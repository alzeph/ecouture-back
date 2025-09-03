from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from users.models import User as UserType

User = get_user_model()


def validate_unique_field(serializer, field_name, value):
    model = serializer.Meta.model
    qs = model.objects.filter(**{field_name: value})
    if serializer.instance:
        qs = qs.exclude(pk=serializer.instance.pk)
    print(qs)
    if qs.exists():
        raise serializers.ValidationError(f"{field_name} must be unique")
    return value


class PermissionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type"]


class GroupReadSerializer(serializers.ModelSerializer):
    permissions = PermissionReadSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]


class UserReadSerializer(serializers.ModelSerializer):
    groups = GroupReadSerializer(many=True, read_only=True)
    user_permissions = PermissionReadSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "photo",
            "last_login",
            "is_staff",
            "is_active",
            "is_superuser",
            "groups",
            "user_permissions",
            "date_joined",
        ]
        read_only_fields = fields


class UserWriteSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            'photo',
            "password",
            "groups",
        ]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": False},
            "phone": {"required": False},
            "start_date": {"required": False},
            "password": {"write_only": True, "required": False},
            "groups": {"write_only": True},
        }
        read_only_fields = [
            "id"
        ]

    def validate(self, attrs):
        for field in ['email', 'phone']:
            if field in attrs:
                attrs[field] = validate_unique_field(self, field, attrs[field])
        return attrs

    def create(self, validated_data) -> UserType:
        groups = validated_data.pop("groups", [])
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if groups:
            user.groups.set(groups)
        return user

    def update(self, instance: UserType, validated_data) -> UserType:
        groups = validated_data.pop("groups", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if groups is not None:
            instance.groups.set(groups)

        return instance


class UserPasswordWrite(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def update(self, instance: UserType, validated_data) -> UserType:
        password = validated_data.get('password', None)
        instance.set_password(password)
        instance.save()
        return instance
