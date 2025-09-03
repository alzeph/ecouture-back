from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError

from haberdashery.models import (
    Haberdashery, TypeArticleInHaberdashery, ArticleInHaberdashery
)

from workshop.models import Worker, Workshop

from haberdashery.serializers import (
    TypeArticleInHaberdasheryWriteSerializer, TypeArticleInHaberdasheryReadSerializer,
    ArticleInHaberdasheryWriteSerializer, HaberdasheryReadSerializer,
    ArticleInHaberdasheryReadSerializer
)

from ecouture.serializers import (
    ExistsResponseSerializer, NotFound404ResponseSerializer,
    VerifyFieldSerializer, ValidationError400Serializer
)

from drf_spectacular.utils import extend_schema
from ecouture.serializers import ExistsResponseSerializer, NotFound404ResponseSerializer


class HaberdasheryMixin:

    def get_haberdashery(self, request: Request) -> Haberdashery:
        try:
            user = request.user
            worker = Worker.objects.get(user=user)
            workshop: Workshop = worker.workshop
            return workshop.haberdashery
        except Haberdashery.DoesNotExist:
            raise ValidationError("Haberdashery not found")

    @extend_schema(
        methods=['get'],
        summary="Voir la haberdashery",
        description="Voir la haberdashery",
        responses={
            200: HaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='haberdasheries',
        url_name='detail',
        permission_classes=[IsAuthenticated]
    )
    def haberdashery(self, request: Request, pk=None):
        haberdashery = self.get_haberdashery(request)
        return Response(HaberdasheryReadSerializer(haberdashery).data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=['post'],
        summary="Voir si le worker est autorisé",
        description="Voir si le worker est autorisé",
        responses={
            200: ExistsResponseSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='worker-authorized',
        url_name='worker-authorized',
        permission_classes=[IsAuthenticated]
    )
    def worker_authorized(self, request: Request, pk=None):
        haberdashery = self.get_haberdashery(request)
        worker_pk = request.data.get('worker_pk')
        if not worker_pk:
            return Response({"detail": "worker_pk is required"}, status=status.HTTP_400_BAD_REQUEST)

        exists = haberdashery.workers.filter(pk=worker_pk).exists()

        return Response({"exists": exists}, status=status.HTTP_200_OK)

    @extend_schema(
        methods=['post'],
        summary="Crée un type d'article",
        description="Crée un type d'article",
        request=TypeArticleInHaberdasheryWriteSerializer,
        responses={
            200: TypeArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['get'],
        summary="Voir tous les types d'article",
        description="Voir tous les types d'article",
        responses={
            200: TypeArticleInHaberdasheryReadSerializer(many=True),
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['post', 'get'],
        url_path='types',
        url_name='type-article-list',
        permission_classes=[IsAuthenticated]
    )
    def type_article_in_haberdashery(self, request: Request, pk=None):

        haberdashery = self.get_haberdashery(request)

        if request.method == 'GET':
            queryset = TypeArticleInHaberdashery.objects.all()
            page = self.paginate_queryset(queryset)
            serializer = TypeArticleInHaberdasheryReadSerializer(
                page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TypeArticleInHaberdasheryWriteSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            type_article_in_haberdashery = serializer.save(
                haberdashery=haberdashery)
        return Response(TypeArticleInHaberdasheryReadSerializer(type_article_in_haberdashery).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['get'],
        summary="Voir un type d'article",
        description="Voir un type d'article",
        responses={
            200: TypeArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="Modifier un type d'article",
        description="Modifier un type d'article",
        request=TypeArticleInHaberdasheryWriteSerializer,
        responses={
            200: TypeArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="Supprimer un type d'article",
        description="Supprimer un type d'article",
        responses={
            200: TypeArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['patch', 'get', 'delete'],
        url_path='types/(?P<type_article_in_haberdashery_pk>[^/.]+)',
        url_name='type-article-detail',
        permission_classes=[IsAuthenticated]
    )
    def type_article_in_haberdashery_detail(self, request: Request, pk=None, type_article_in_haberdashery_pk=None):

        haberdashery = self.get_haberdashery(request)

        try:
            type_article = haberdashery.type_articles.filter(
                pk=type_article_in_haberdashery_pk).first()
        except:
            return Response({"detail": "Type article not found oh"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = TypeArticleInHaberdasheryReadSerializer(type_article)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'PATCH' or request.method == 'PUT':
            serializer = TypeArticleInHaberdasheryWriteSerializer(
                type_article, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                serializer.save()
            return Response(TypeArticleInHaberdasheryReadSerializer(type_article).data, status=status.HTTP_200_OK)

        with transaction.atomic():
            type_article.is_delete = True
            type_article.save(update_fields=['is_delete'])
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        url_name="type-article-name-unique",
        permission_classes=[IsAuthenticated]
    )
    def type_article_names_unique(self, request: Request, pk=None):
        verify_name = request.data.get('verify', None)
        exclude_name = request.data.get('exclude', None)
        if not verify_name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        type_article = TypeArticleInHaberdashery.objects.all()
        if exclude_name:
            type_article = type_article.exclude(name=exclude_name)
        exists = type_article.filter(name=verify_name).exists()
        return Response({"exists": exists})


    @extend_schema(
        methods=['post'],
        summary="Crée un article",
        description="Crée un article",
        request=ArticleInHaberdasheryWriteSerializer,
        responses={
            200: ArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['get'],
        summary="Voir tous les articles",
        description="Voir tous les articles",
        responses={
            200: ArticleInHaberdasheryReadSerializer(many=True),
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['post', 'get'],
        url_path='articles',
        url_name='articles-list',
        permission_classes=[IsAuthenticated]
    )
    def article_in_haberdashery(self, request: Request, pk=None):

        haberdashery = self.get_haberdashery(request)

        if request.method == 'GET':
            queryset = ArticleInHaberdashery.objects.all()
            page = self.paginate_queryset(queryset)
            serializer = ArticleInHaberdasheryReadSerializer(
                page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ArticleInHaberdasheryWriteSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            article_in_haberdashery = serializer.save()
        return Response(ArticleInHaberdasheryReadSerializer(article_in_haberdashery).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        methods=['get'],
        summary="Voir un article",
        description="Voir un article",
        responses={
            200: ArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['patch'],
        summary="Modifier un article",
        description="Modifier un article",
        request=ArticleInHaberdasheryWriteSerializer,
        responses={
            200: ArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @extend_schema(
        methods=['delete'],
        summary="Supprimer un article",
        description="Supprimer un article",
        responses={
            200: ArticleInHaberdasheryReadSerializer,
            404: NotFound404ResponseSerializer
        }
    )
    @action(
        detail=False,
        methods=['patch', 'get', 'delete'],
        url_path='articles/(?P<article_in_haberdashery_pk>[^/.]+)',
        url_name='articles-detail',
        permission_classes=[IsAuthenticated]
    )
    def article_in_haberdashery_detail(self, request: Request, pk=None, article_in_haberdashery_pk=None):

        haberdashery = self.get_haberdashery(request)

        try:
            article = ArticleInHaberdashery.objects.filter(
                type_article__haberdashery=haberdashery, pk=article_in_haberdashery_pk).first()
        except:
            return Response({"detail": "Article not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = ArticleInHaberdasheryReadSerializer(article)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'PATCH' or request.method == 'PUT':
            serializer = ArticleInHaberdasheryWriteSerializer(
                article, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                serializer.save()
            return Response(ArticleInHaberdasheryReadSerializer(article).data, status=status.HTTP_200_OK)

        with transaction.atomic():
            article.is_delete = True
            article.save(update_fields=['is_delete'])
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        url_path=r"article-names-unique/(?P<type_article_in_haberdashery_pk>[^/.]+)",
        url_name="article-name-unique",
        permission_classes=[IsAuthenticated]
    )
    def article_names_unique(self, request: Request, pk=None, type_article_in_haberdashery_pk=None):
        verify_name = request.data.get('verify', None)
        exclude_name = request.data.get('exclude', None)

        try:
            type_article = TypeArticleInHaberdashery.objects.get(pk=type_article_in_haberdashery_pk)
        except:
            return Response({"detail": "Type article not found"}, status=status.HTTP_404_NOT_FOUND)

        if not verify_name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)
        articles = type_article.articles.all()
        if exclude_name:
            articles = articles.exclude(name=exclude_name)
        exists = articles.filter(name=verify_name).exists()
        return Response({"exists": exists})
