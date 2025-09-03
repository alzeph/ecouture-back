from haberdashery.models import TypeArticleInHaberdashery, ArticleInHaberdashery,  Haberdashery
from rest_framework import serializers
from workshop.serializers.read import WorkerReadSerializer


class HaberdasheryReadSerializer(serializers.ModelSerializer):
    workers = WorkerReadSerializer(many=True)
    class Meta:
        model = Haberdashery
        fields = [
            'workers',
            'is_active',
            'end_date',
        ]


class TypeArticleInHaberdasheryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeArticleInHaberdashery
        fields = [
            'pk',
            'name',
            'slug',
            'description',
            'is_delete'
        ]


class ArticleInHaberdasheryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleInHaberdashery
        fields = [
            'pk',
            'type_article',
            'name',
            'quantity',
            'is_delete',
            'is_out',
            'createdAt',
            'updatedAt'
        ]


# seriliazer write


class TypeArticleInHaberdasheryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeArticleInHaberdashery
        fields = [
            'name',
            'description',
            'is_delete',
        ]
        extra_kwargs = {
            'is_delete': {'required': False, 'read_only': True}
        }


class ArticleInHaberdasheryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleInHaberdashery
        fields = [
            'type_article',
            'name',
            'quantity',
            'is_delete',
            'is_out'
        ]
        
        extra_kwargs = {
            'is_delete': {'required': False, 'read_only': True},
            'is_out': {'required': False}
        }





