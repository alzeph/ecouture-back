# tests/test_workshop_viewset.py
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from workshop.models import (
    Worker, CustomerWorkshop, Workshop, OrderWorkshop,
    OrderWorkshopGroup, Fitting, Setting, PackageHistory
)
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.utils import timezone
from workshop.utils import init_package



def get_test_image_file(filename="test_image.png"):
    """
    Retourne un fichier image temporaire valide pour les tests.
    """
    # Crée une image 1x1 pixel en mémoire
    image = Image.new('RGB', (1, 1), color=(255, 0, 0))
    file_io = BytesIO()
    image.save(file_io, format='PNG')
    file_io.seek(0)

    # Vérifie que filename a une extension
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        filename += '.png'

    return SimpleUploadedFile(
        name=filename,
        content=file_io.read(),
        content_type='image/png'
    )


class WorkshopViewSetTestCase(TestCase):

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

        self.user_worker2 = User.objects.create_user(
            email="test_worker1@example.com",
            phone="1234567894",
            password="password123",
            first_name="John",
            last_name="Doe"
        )

        self.worker1 = Worker.objects.create(
            user=self.user_worker1,
            workshop=self.workshop,
            is_owner=True
        )

        self.worker2 = Worker.objects.create(
            user=self.user_worker2,
            workshop=self.workshop
        )

        self.customer1 = CustomerWorkshop.objects.create(
            last_name="Smith",
            first_name="John",
            nickname="JohnSmith",
            genre="MAN",
            email="test1@example.com",
            phone="1234567891",
            workshop=self.workshop,
            photo=get_test_image_file(filename="customer_file_1")
        )

        self.customer2 = CustomerWorkshop.objects.create(
            last_name="Doe",
            first_name="Jane",
            nickname="JaneDoe",
            genre="WOMAN",
            email="test2@example.com",
            phone="1234567892",
            workshop=self.workshop,
            photo=get_test_image_file(filename="customer_file_2")
        )

        self.order = OrderWorkshop.objects.create(
            customer=self.customer1,
            worker=self.worker1,
            gender="MAN",
            type_of_clothing="SHIRT",
            measurement={},
            description_of_fabric="This is a test fabric",
            photo_of_fabric=get_test_image_file(filename="order_file_1"),
            clothing_model="This is a test model",
            description_of_model="This is a test model",
            photo_of_clothing_model=get_test_image_file(
                filename="order_file_2"),
            amount=100,
            down_payment=50,
            is_urgent=False,
            estimated_delivery_date="2023-01-01",
            promised_delivery_date="2023-01-01",
        )

        self.order_group = OrderWorkshopGroup(
            description="This is a test group",
        )
        self.order_group = OrderWorkshopGroup.objects.create(
            description="This is a test group"
        )
        self.order_group.orders.set([self.order])

        self.fitting = Fitting.objects.create(
            order=self.order,
            scheduled_date=timezone.now(),
        )

        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user_worker1)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        self.workshop.settings.worker_authorization_is_order.set([
                                                                 self.worker2.pk])
        self.workshop.settings.worker_authorization_is_fitting.set([
                                                                   self.worker2.pk])
        self.workshop.settings.worker_authorization_is_customer.set([
                                                                    self.worker2.pk])
        self.workshop.settings.worker_authorization_is_worker.set([
                                                                  self.worker2.pk])
        self.workshop.settings.worker_authorization_is_setting.set([
                                                                   self.worker2.pk])
    # Tests CRUD Workshop

    def test_create_workshop(self):
        data = {
            'workshop': {
                'name': 'Test Workshop true',
                'description': 'This is a test workshop',
                'email': 'test2@example.com',
                'phone': '1234567892',
                'country': 'FR',
                'city': 'Paris',
                'address': '123 Rue de la Paix',
            },
            'user': {
                'email': 'test2@example.com',
                'phone': '1234567892',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
            }
        }
        url = reverse('workshops-list')
        response = self.client.post(url, data, format='json')
        # print("176 =>", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workshop.objects.count(), 2)

    def test_retrieve_workshop(self):
        url = reverse('workshops-detail', kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.workshop.name)

    def test_update_workshop(self):
        data = {
            'email': 'test_replace@example.com',
        }
        url = reverse('workshops-detail', kwargs={'pk': self.workshop.pk})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], data['email'])

    def test_workshop_validators_names_unique(self):
        data = {
            "verify": self.workshop.name
        }
        url = reverse('workshops-name-unique')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_package_list(self):
        url = reverse('workshops-packages-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    # # Tests WorkerMixin

    def test_worker_list(self):
        url = reverse('workshops-workers-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data['results'], list)

    def test_worker_create(self):
        data = {
            'user': {
                'email': 'test_worker2@example.com',
                'phone': '1234567892',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                # 'photo': get_test_image_file(filename="worker_file_2"),
            }
        }
        url = reverse('workshops-workers-list', kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(Worker.objects.count(), 2)

    def test_worker_detail_retrieve(self):
        url = reverse('workshops-workers-detail',
                      kwargs={'pk': self.workshop.pk, 'worker_pk': self.worker2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']
                         ['email'], self.worker2.user.email)

    def test_worker_detail_update_photo(self):
        data = {
            'photo': get_test_image_file(filename="worker_file_2"),
        }
        url = reverse('workshops-workers-detail',
                      kwargs={'pk': self.workshop.pk, 'worker_pk': self.worker2.pk})
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_worker_detail_delete(self):
        url = reverse('workshops-workers-detail',
                      kwargs={'pk': self.workshop.pk, 'worker_pk': self.worker2.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # # Tests CustomerWorkshopMixin
    def test_customer_list(self):
        url = reverse('workshops-customers-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data['results'], list)

    def test_customer_create(self):
        data = {
            'last_name': 'Doe',
            'first_name': 'John',
            'nickname': 'JohnDoe',
            'genre': 'MAN',
            'email': 'test_customer_true@example.com',
            'phone': '0000000001',
        }
        url = reverse('workshops-customers-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(CustomerWorkshop.objects.count(), 2)

    def test_customer_detail_retrieve(self):
        url = reverse('workshops-customers-detail',
                      kwargs={'pk': self.workshop.pk, 'customer_pk': self.customer1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.customer1.email)

    def test_customer_detail_update_photo(self):
        data = {
            "photo": get_test_image_file(filename="customer_file_2"),
        }
        url = reverse('workshops-customers-detail',
                      kwargs={'pk': self.workshop.pk, 'customer_pk': self.customer1.pk})
        response = self.client.patch(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_detail_delete(self):
        url = reverse('workshops-customers-detail',
                      kwargs={'pk': self.workshop.pk, 'customer_pk': self.customer1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # # Tests OrderWorkshopMixin
    def test_order_list(self):
        url = reverse('workshops-orders-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data['results'], list)

    def test_order_create(self):
        data = {
            'customer': self.customer1.pk,
            'worker': self.worker2.pk,
            'type_of_clothing':  OrderWorkshop.TypeOfClothing.SHIRT,
            'gender': 'MAN',
            'measurement': {
                'chest': 80,
                'waist': 60,
                'arm': 20,
                'height': 180,
                'shoulder': 40,
                'sleeve': 20,
            },
            'description_of_fabric': 'Cotton',
            'clothing_model': 'T-Shirt',
            'description_of_model': 'Basic T-Shirt',
            'amount': 100,
            'down_payment': 50,
            'estimated_delivery_date': '2022-12-31',
            'promised_delivery_date': '2022-12-31',
        }

        url = reverse('workshops-orders-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, data, format='json' )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(OrderWorkshop.objects.count(), 2)

    def test_order_detail_retrieve(self):
        url = reverse('workshops-orders-detail',
                      kwargs={'pk': self.workshop.pk, 'order_pk': self.order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer']['id'], self.customer1.pk)

    def test_order_detail_update_photo(self):
        data = {
            'photo_of_fabric': get_test_image_file(filename="order_file_2"),
            'photo_of_clothing_model': get_test_image_file(filename="order_file_2"),   
        }
        url = reverse('workshops-orders-detail',
                      kwargs={'pk': self.workshop.pk, 'order_pk': self.order.pk})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_detail_delete(self):
        url = reverse('workshops-orders-detail',
                      kwargs={'pk': self.workshop.pk, 'order_pk': self.order.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Tests OrderWorkshopGroupMixin
    def test_order_group_list(self):
        url = reverse('workshops-order-groups-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data['results'], list)

    def test_order_group_create(self):
        data = {
            "description": "Test group",
            "orders": [self.order.pk],
        }
        url = reverse('workshops-order-groups-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(OrderWorkshopGroup.objects.count(), 1)

    def test_order_group_detail_retrieve(self):
        url = reverse('workshops-order-groups-detail',
                      kwargs={'pk': self.workshop.pk, 'order_group_pk': self.order_group.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'],
                         self.order_group.description)

    def test_order_group_detail_update(self):
        data = {
            "description": "Test group updated",
        }
        url = reverse('workshops-order-groups-detail',
                      kwargs={'pk': self.workshop.pk, 'order_group_pk': self.order_group.pk})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], data['description'])

    def test_order_group_detail_delete(self):
        url = reverse('workshops-order-groups-detail',
                      kwargs={'pk': self.workshop.pk, 'order_group_pk': self.order_group.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Tests FittingMixin
    def test_fitting_create(self):
        data = {
            "order": self.order.pk,
            "scheduled_date": "2022-12-31 16:00:00",
        }
        url = reverse('workshops-fittings-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(Fitting.objects.count(), 1)

    def test_fitting_detail_update(self):
        data = {
            "actual_date": "2022-12-31 16:00:00",
            "note": "Test note",
            "status": Fitting.FittingStatus.NEEDS_MAJOR_ADJUSTMENTS
        }
        url = reverse('workshops-fittings-detail',
                      kwargs={'pk': self.workshop.pk, 'fitting_pk': self.fitting.pk})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], data['status'])

    def test_fitting_detail_delete(self):
        url = reverse('workshops-fittings-detail',
                      kwargs={'pk': self.workshop.pk, 'fitting_pk': self.fitting.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # Tests SettingMixin

    def test_setting_update(self):
        data = {
            "worker_authorization_is_order": [self.order.pk],
        }
        url = reverse('workshops-settings-detail',
                      kwargs={"pk": self.workshop.pk})
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # verifier des autorisation de l'atelier lié au type de package choisi

    def test_worker_authorised_is_create(self):
        url = reverse('workshops-settings-worker-count-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_customer_authorised_is_create(self):
        url = reverse('workshops-settings-customer-count-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_order_authorised_is_create(self):
        url = reverse('workshops-settings-order-count-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_fitting_authorised_is_create(self):
        url = reverse('workshops-settings-fitting-count-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    # verifiatiion des autoriration lier a chauqe worker de l'atelier

    def test_worker_is_authorisation_is_order(self):
        url = reverse('workshops-settings-order-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, {"worker_pk": self.worker2.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_worker_is_authorisation_is_customer(self):
        url = reverse('workshops-settings-customer-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, {"worker_pk": self.worker2.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_worker_is_authorisation_is_fitting(self):
        url = reverse('workshops-settings-fitting-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, {"worker_pk": self.worker2.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_worker_is_authorisation_is_worker(self):
        url = reverse('workshops-settings-worker-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, {"worker_pk": self.worker2.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    def test_worker_is_authorisation_is_setting(self):
        url = reverse('workshops-settings-setting-authorised',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.post(url, {"worker_pk": self.worker2.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['exists'], True)

    # Tests PackageHistoryMixin
    def test_package_history_list(self):
        url = reverse('workshops-package-histories-list',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIsInstance(response.data['results'], list)

    # Tests StatMixin
    def test_stat_orders_workshop(self):
        url = reverse('workshops-stats-orders',
                      kwargs={'pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_stat_customers_workshop(self):
    #     pass
