from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from notifications.models import InternalNotification, ExternalNotification
from workshop.models import CustomerWorkshop, Workshop, Worker, OrderWorkshopGroup, OrderWorkshop, Fitting
from django.utils import timezone
from users.models import User
from workshop.utils import init_package


class NotificationAPITestCase(TestCase):
    def setUp(self):
        # Créer un utilisateur
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
        )

        self.customer2 = CustomerWorkshop.objects.create(
            last_name="Doe",
            first_name="Jane",
            nickname="JaneDoe",
            genre="WOMAN",
            email="test2@example.com",
            phone="1234567892",
            workshop=self.workshop,
        )

        self.order = OrderWorkshop.objects.create(
            customer=self.customer1,
            worker=self.worker1,
            gender="MAN",
            type_of_clothing="SHIRT",
            measurement={},
            description_of_fabric="This is a test fabric",
            clothing_model="This is a test model",
            description_of_model="This is a test model",
            
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

    # Créer quelques notifications internes
        self.internal1 = InternalNotification.objects.create(
            user=self.user_worker1,
            type='info',
            title='Info 1',
            message='Message 1'
        )
        self.internal2 = InternalNotification.objects.create(
            user=self.user_worker1,
            type='warning',
            title='Warning 1',
            message='Message 2'
        )

        # Créer quelques notifications externes
        self.external1 = ExternalNotification.objects.create(
            customer=self.customer1,
            type='email',
            title='External 1',
            message='Message ext 1'
        )

        # Client API avec JWT
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.worker1)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_internal_notifications(self):
        url = reverse('notifications-internal-get')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 2)  # deux notifications non lues

    def test_patch_internal_notification(self):
        url = reverse('notifications-internal-update',
                      kwargs={'notification_id': self.internal1.pk})
        response = self.client.patch(url, {'is_read': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.internal1.refresh_from_db()
        self.assertTrue(self.internal1.is_read)
        # read_at doit être mis à jour
        self.assertIsNotNone(self.internal1.read_at)

    def test_get_external_notifications(self):
        url = reverse('notifications-external', kwargs={'workshop_pk': self.workshop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
