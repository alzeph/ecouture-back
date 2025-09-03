from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from workshop.models import Worker, Workshop

from haberdashery.models import (
    Haberdashery, TypeArticleInHaberdashery, ArticleInHaberdashery
)

from workshop.utils import init_package

class HaberdasheryViewSetTest(TestCase):

    def setUp(self):
        init_package()

        self.workshop = Workshop.objects.create(
            name="Test Workshop",
            description="This is a test workshop",
            email="test1@example.com",
            phone="1234567891",
            country="FR",
            city="Paris",
            address="123 Rue de la Paix",
        )

        self.user_worker1 = User.objects.create_user(
            email="test1@example.com",
            phone="1234567891",
            password="password123",
            first_name="John",
            last_name="Doe"
        )

        self.worker1 = Worker.objects.create(
            user=self.user_worker1,
            workshop=self.workshop,
            is_owner=True
        )

        self.haberdashery, _ = Haberdashery.objects.get_or_create(workshop=self.workshop)
        
        self.type_article_in_haberdashery = TypeArticleInHaberdashery.objects.create(
            haberdashery=self.haberdashery,
            name="Test Type Article In Haberdashery",
            description="This is a test type article in haberdashery",
        )
        
        self.article_in_haberdashery = ArticleInHaberdashery.objects.create(
            name="Test Article In Haberdashery",
            type_article=self.type_article_in_haberdashery,
            quantity=10,
        )
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user_worker1)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_retrieve_haberdashery(self):
        url = reverse('haberdasheries-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('workers', response.data)

    def test_worker_authorized(self):
        url = reverse('haberdasheries-worker-authorized')
        response = self.client.post(url, {'worker_pk': self.worker1.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('exists', response.data)
        self.assertFalse(response.data['exists'])

    # Type Article
    def test_type_article_in_haberdashery_create(self):
        data = {
            "name": "Test Type Article In Haberdashery 2",
            "description": "This is a test type article in haberdashery",
        }
        url = reverse('haberdasheries-type-article-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], data['name'])
        
    def test_type_article_in_haberdashery_list(self):
        url = reverse('haberdasheries-type-article-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_type_article_in_haberdashery_detail(self):
        url = reverse('haberdasheries-type-article-detail',
                      kwargs={'type_article_in_haberdashery_pk': self.type_article_in_haberdashery.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], self.type_article_in_haberdashery.name)

    def test_type_article_in_haberdashery_patch(self):
        data = {
            "name": "Test Type Article In Haberdashery Updated",
            "description": "This is a test type article in haberdashery updated",
        }
        url = reverse('haberdasheries-type-article-detail',
                      kwargs={'type_article_in_haberdashery_pk': self.type_article_in_haberdashery.pk})
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], data['name'])

    def test_type_article_names_unique(self):
        data = {
            "verify": self.type_article_in_haberdashery.name
        }
        url = reverse('haberdasheries-type-article-name-unique')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)
    
    
    # Article In Haberdashery

    def test_article_in_haberdashery_create(self):
        data = {
            "name": "Test Article In Haberdashery 1",
            "quantity": 10,
            "type_article": self.type_article_in_haberdashery.pk
        } 
        url = reverse("haberdasheries-articles-list")
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], data['name'])
        
    def test_article_in_haberdashery_list(self):
        url = reverse("haberdasheries-articles-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)
    
    def test_article_in_haberdashery_detail(self):
        url = reverse('haberdasheries-articles-detail',
                      kwargs={'article_in_haberdashery_pk': self.article_in_haberdashery.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], self.article_in_haberdashery.name)
        
    def test_article_in_haberdashery_patch(self):
        data = {
            "name": "Test Article In Haberdashery Updated",
            "quantity": 10,
            "type_article": self.type_article_in_haberdashery.pk
        }
        url = reverse('haberdasheries-articles-detail',
                      kwargs={'article_in_haberdashery_pk': self.article_in_haberdashery.pk})
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], data['name'])
    
    def test_article_names_unique(self):
        data = {
            "verify": self.article_in_haberdashery.name
        }
        url = reverse('haberdasheries-article-name-unique', 
                      kwargs={
                          'type_article_in_haberdashery_pk': self.type_article_in_haberdashery.pk})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)
    
    