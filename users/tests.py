from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from unittest.mock import patch
from rest_framework import status
from django.contrib.auth.models import Group, Permission
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User, UserPasswordReset
import datetime


class UserViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email="test@example.com",
            phone="1234567890",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        # Créer un autre utilisateur pour test d'exclusion
        self.user2 = User.objects.create_user(
            email="other@example.com",
            phone="0987654321",
            password="password123",
            first_name="Jane",
            last_name="Doe"
        )
        # Créer token JWT
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        # Créer groupe et permission
        self.group = Group.objects.create(name="TestGroup")
        self.permission = Permission.objects.first()  # juste pour test

    # ------------------ Endpoints AllowAny ------------------
    def test_verify_email_exists(self):
        response = self.client.post("/api/user/verify-email/", {"verify": "test@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["exists"])

    def test_verify_email_not_exists(self):
        response = self.client.post("/api/user/verify-email/", {"verify": "nonexistent@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["exists"])

    def test_verify_phone_exists(self):
        response = self.client.post("/api/user/verify-phone/", {"verify": "1234567890"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["exists"])
        
    def test_verify_phone_not_exists(self):
        response = self.client.post("/api/user/verify-phone/", {"verify": "1111111111"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["exists"])

    def test_groups_list(self):
        response = self.client.get("/api/user/groups/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_permissions_list(self):
        response = self.client.get("/api/user/user-permissions/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    # ------------------ Endpoints JWT ------------------
    def test_modify_users_success(self):
        data = {"first_name": "Updated"}
        response = self.client.patch(f"/api/user/modify/{self.user.id}/", data, **self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_modify_password_success(self):
        data = {"password": "newpassword123"}
        response = self.client.patch(f"/api/user/modify-password/{self.user.id}/", data, **self.auth_header)
        self.assertEqual(response.status_code, 200)
        # Vérifier que le mot de passe a bien été changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_verify_password_actual_correct(self):
        data = {"password": "password123"}
        response = self.client.post(f"/api/user/verify-password-actual/{self.user.id}/", data, **self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["result"])

    def test_verify_password_actual_wrong(self):
        data = {"password": "wrongpassword"}
        response = self.client.post(f"/api/user/verify-password-actual/{self.user.id}/", data, **self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["result"])

    # ------------------ Mot de passe oublié / reset ------------------
    @patch("users.mixins.send_mail")
    def test_forgot_password_creates_token(self, mock_send):
        data = {"email": "test@example.com"}
        response = self.client.post("/api/user/forgot-password/", data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("detail", response.data)
        token_obj = UserPasswordReset.objects.filter(user=self.user).first()
        self.assertIsNotNone(token_obj)
        # Vérifier que send_mail a été appelé
        mock_send.assert_called_once()

    def test_reset_password_with_valid_token(self):
        token = "testtoken"
        expiry = timezone.now() + datetime.timedelta(hours=1)
        UserPasswordReset.objects.create(user=self.user, token=token, expiry=expiry)
        data = {"token": token, "new_password": "newpassword456"}
        response = self.client.post("/api/user/reset-password/", data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))

    def test_reset_password_with_expired_token(self):
        token = "expiredtoken"
        expiry = timezone.now() - datetime.timedelta(hours=1)
        UserPasswordReset.objects.create(user=self.user, token=token, expiry=expiry)
        data = {"token": token, "new_password": "newpassword456"}
        response = self.client.post("/api/user/reset-password/", data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Token expired")
