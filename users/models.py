from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission, Group
from django.db import models

GROUPS = {
    "WORKERS": "WORKERS",
    "TAILORS": "TAILORS",
    "ADMIN": "ADMIN",
    "CUSTOMERS_WORKSHOPS": "CUSTOMERS_WORKSHOPS",
    "CUSTOMERS_SHOP": "CUSTOMERS_SHOP",
}


class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        if not phone:
            raise ValueError("Le numéro de téléphone est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Utilisateur système Django
    Peut être propriétaire d'atelier
    ou tailleur ou admin
    """

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    phone = models.CharField(max_length=20, unique=True)
    photo = models.ImageField(upload_to='users/photos/', null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, blank=True)
    user_permissions = models.ManyToManyField(Permission, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']


class UserPasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
