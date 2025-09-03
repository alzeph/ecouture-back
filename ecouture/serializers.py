from rest_framework import serializers


class ExistsResponseSerializer(serializers.Serializer):
    exists = serializers.BooleanField()


class VerifyFieldSerializer(serializers.Serializer):
    verify = serializers.EmailField()
    exclude = serializers.EmailField(required=False)


class NotFound404ResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ValidationError400Serializer(serializers.Serializer):
    field_name = serializers.ListField(
        child=serializers.CharField(),
        help_text="Liste des messages d'erreur liés à ce champ."
    )

class WorkerAuthorisationSerializer(serializers.Serializer):
    worker_pk = serializers.IntegerField()