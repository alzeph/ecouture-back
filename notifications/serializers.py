from rest_framework import serializers
from django.utils import timezone
from notifications.models import InternalNotification, ExternalNotification

class InternalNotificatinoReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading InternalNotification data.
    """
    class Meta:
        model = InternalNotification
        fields = ['id', 'type', 'read_at', 'category', 'title', 'message', 'is_read', 'createdAt']
        read_only_fields = ['id', 'createdAt']
        

class InternalNotificationWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for writing InternalNotification data.
    """
    class Meta:
        model = InternalNotification
        fields = ['is_read']
        read_only_fields = ['id', 'createdAt']
        
    def update(self, instance, validated_data):
        # Mettre à jour is_read
        instance.is_read = validated_data.get('is_read', instance.is_read)
        
        # Si la notification est marquée comme lue et read_at vide, mettre la date actuelle
        if instance.is_read and not instance.read_at:
            instance.read_at = timezone.now()
        instance.save()
        return instance
    


class ExternalNotificationReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading ExternalNotification data.
    """
    class Meta:
        model = ExternalNotification
        fields = ['id', 'type', 'scheduled_for', 'title', 'message', 'is_sent']
        read_only_fields = ['id']