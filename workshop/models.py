from django.db.models import Max
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
import time

User = get_user_model()


class Package(models.Model):

    class PackageType(models.TextChoices):
        DEMO = "DEMO", "Demo"
        BASIC = "BASIC", "Basic"
        PREMIUM = "PREMIUM", "Premium"
        PRO = "PRO", "Pro"

    name = models.CharField(
        max_length=255, choices=PackageType.choices, unique=True)
    description = models.TextField()
    features = models.JSONField()  # une liste de string
    price = models.DecimalField(max_digits=10, decimal_places=0)
    duration = models.DurationField()
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    PACKAGE_LIMITS = {
        PackageType.DEMO: dict(max_workers=5, max_orders=50, max_customers=50, max_fittings=50, max_order_groups=10),
        PackageType.BASIC: dict(max_workers=15, max_orders=500, max_customers=500, max_fittings=100, max_order_groups=50),
        PackageType.PREMIUM: dict(max_workers=30, max_orders=2000, max_customers=5000, max_fittings=300, max_order_groups=200),
        PackageType.PRO: dict(max_workers=100, max_orders=10000, max_customers=20000, max_fittings=1000, max_order_groups=500),
    }

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"


class Workshop(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, primary_key=True)
    description = models.TextField()
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("name", "email"),
            ("name", "phone")
        ]

    def __str__(self):
        return self.name
    
    def get_owners(self):
        return Worker.objects.filter(workshop=self, is_owner=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PackageHistory(models.Model):
    """
    Historique des packages d'un atelier.
    Permet de garder une trace des anciens packages choisis.
    """

    workshop = models.ForeignKey(
        "Workshop",
        on_delete=models.CASCADE,
        related_name="package_histories"
    )

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    info_paiement = models.JSONField(null=True, blank=True)

    # Dates de début et de fin du package
    is_active = models.BooleanField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Date de création de l'entrée historique
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("workshop", "name", "start_date")
        ]

    def __str__(self):
        return f"{self.workshop.name} - {self.name} | ({self.start_date} → {self.end_date})"

    def save(self, *args, **kwargs):
        if not self.pk:
            PackageHistory.objects.filter(
                workshop=self.workshop).update(is_active=False)
            self.is_active = True
        super().save(*args, **kwargs)


class Worker(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="worker"
    )
    workshop = models.ForeignKey(
        "Workshop",
        on_delete=models.CASCADE,
        related_name="workers"
    )
    is_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_allowed = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Worker: {self.user} at {self.workshop}"


class CustomerWorkshop(models.Model):

    class Gender(models.TextChoices):
        MAN = "MAN", "Homme"
        WOMAN = "WOMAN", "Femme"
        CHILDREN = "CHILDREN", "Enfant"

    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, unique=True)
    genre = models.CharField(max_length=8, choices=Gender.choices)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    workshop = models.ForeignKey(
        "Workshop",
        on_delete=models.CASCADE,
        related_name="customers"
    )
    photo = models.ImageField(
        upload_to="customers_workshop/photos",
        null=True,
        blank=True,
        help_text="Photo du client, optionnelle"
    )
    is_active = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ("phone", "workshop"),
            ("nickname", "last_name", "first_name")
        )

    def __str__(self):
        return f"{self.nickname} ({self.last_name} {self.first_name})"


class OrderWorkshop(models.Model):
    class Gender(models.TextChoices):
        MAN = "MAN", "Man"
        WOMAN = "WOMAN", "Woman"
        CHILDREN = "CHILDREN", "Children"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    class OrderStatus(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        DELETED = "DELETED", "Deleted"  # jamais supprimer réellement

    class TypeOfClothing(models.TextChoices):
        SHIRT = "SHIRT", "Shirt"
        PANTS = "PANTS", "Pants"
        DRESS = "DRESS", "Dress"

    number = models.CharField(
        max_length=50, unique=True, editable=False, blank=True)
    customer = models.ForeignKey(
        "CustomerWorkshop", on_delete=models.CASCADE, related_name="orders")
    worker = models.ForeignKey(
        "Worker", on_delete=models.CASCADE, related_name="orders")
    gender = models.CharField(max_length=8, choices=Gender.choices)
    type_of_clothing = models.CharField(
        max_length=20, choices=TypeOfClothing.choices)
    description = models.TextField(blank=True, null=True)
    measurement = models.JSONField()
    description_of_fabric = models.CharField(max_length=255)
    photo_of_fabric = models.ImageField(
        upload_to="orders_photos/photo_of_fabric", null=True, blank=True)
    clothing_model = models.CharField(max_length=255)
    description_of_model = models.TextField(null=True, blank=True)
    photo_of_clothing_model = models.ImageField(
        upload_to="orders_photos/photo_of_clothing_model", null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices)
    status = models.CharField(max_length=15, choices=OrderStatus.choices)
    is_urgent = models.BooleanField(default=False)
    assign_date = models.DateField(null=True, blank=True)
    # commande “supprimée” sans supprimer
    is_deleted = models.BooleanField(default=False)
    estimated_delivery_date = models.DateField()
    promised_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.down_payment > self.amount:
            raise ValidationError(
                "Le montant de l'acompte ne peut pas dépasser le montant total.")
        if self.customer.workshop_id != self.worker.workshop_id:
            raise ValidationError(
                "Le client et l'ouvrier doivent appartenir au même atelier.")
        if self.promised_delivery_date < self.estimated_delivery_date:
            raise ValidationError(
                "La date promise doit être après ou égale à la date estimée.")
        if self.actual_delivery_date and self.actual_delivery_date < self.estimated_delivery_date:
            raise ValidationError(
                "La date réelle ne peut pas être avant la date estimée.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            self.assign_date = timezone.now().date()
            self.status = self.OrderStatus.NEW
        else:
            old_worker_id = OrderWorkshop.objects.filter(
                pk=self.pk).values_list("worker_id", flat=True).first()
            if old_worker_id is not None and old_worker_id != self.worker_id:
                self.assign_date = timezone.now().date()

        if not self.number:
            last_order = OrderWorkshop.objects.order_by('-id').first()
            last_id = last_order.id if last_order else 0
            next_id = last_id + 1
            self.number = f"{str(int(time.time()*1000))[-10:]}"

        # Met à jour le statut de paiement
        if self.down_payment == 0:
            self.payment_status = self.PaymentStatus.PENDING
        elif self.down_payment < self.amount:
            self.payment_status = self.PaymentStatus.PARTIAL
        else:
            self.payment_status = self.PaymentStatus.PAID

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.number} for {self.customer.nickname}"


class OrderWorkshopGroup(models.Model):
    """
    Groupement de commandes (famille, mariage…) pour facturation groupée.
    """

    # Numéro unique du groupement
    number = models.CharField(max_length=30, unique=True, editable=False)
    description = models.CharField(max_length=255)

    # Commandes incluses dans ce groupement
    orders = models.ManyToManyField(
        "OrderWorkshop",
        related_name="groups",
        blank=True,
        help_text="Commandes incluses dans ce groupement",
    )

    # Total des montants des commandes du groupement
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, blank=True
    )

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Génère un identifiant unique si absent
        if not self.number:
            last_order = OrderWorkshop.objects.order_by('-id').first()
            last_id = last_order.id if last_order else 0
            next_id = last_id + 1
            self.number = f"{str(int(time.time()*1000))[-10:]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number


class Fitting(models.Model):
    """
    Fitting associé à une commande pour ajustement sur le client.
    """

    class FittingStatus(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"  # Fitting programmé
        COMPLETED = "COMPLETED", "Completed"  # Fitting terminé
        CANCELLED = "CANCELLED", "Cancelled"  # Fitting annulé
        # Ajustements importants nécessaires
        NEEDS_MAJOR_ADJUSTMENTS = "NEEDS_MAJOR_ADJUSTMENTS", "Needs Major Adjustments"

    order = models.ForeignKey(
        "OrderWorkshop",
        on_delete=models.CASCADE,
        related_name="fittings"
    )

    # Numéro du fitting pour la commande (auto-incrémenté)
    fitting_number = models.PositiveIntegerField(blank=True)
    scheduled_date = models.DateTimeField()
    actual_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    adjustments_needed = models.TextField(null=True, blank=True)

    # Statut du fitting
    status = models.CharField(
        max_length=30,
        choices=FittingStatus.choices,
        default=FittingStatus.SCHEDULED
    )

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("order", "fitting_number")

    def save(self, *args, **kwargs):
        # Attribue automatiquement le numéro du fitting si absent
        if not self.fitting_number:
            last_num = (
                Fitting.objects.filter(order=self.order)
                .aggregate(max_num=Max("fitting_number"))
                .get("max_num") or 0
            )
            self.fitting_number = last_num + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fitting #{self.fitting_number} for {self.order.number}"


class Setting(models.Model):
    """
    Paramètres généraux de l'atelier et limites selon le 
    """

    workshop = models.OneToOneField(
        Workshop,
        on_delete=models.CASCADE,
        related_name="settings"
    )

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Limites selon le package
    max_workers = models.PositiveIntegerField(default=5)
    max_orders = models.PositiveIntegerField(default=50)
    max_customers = models.PositiveIntegerField(default=50)
    max_fittings = models.PositiveIntegerField(default=50)
    max_order_groups = models.PositiveIntegerField(default=10)
    max_order_ongoing_by_worker = models.PositiveBigIntegerField(default=5)

    # Permissions par worker
    worker_authorization_is_order = models.ManyToManyField(
        "Worker", blank=True, related_name="worker_authorization_is_order"
    )
    worker_authorization_is_fitting = models.ManyToManyField(
        "Worker", blank=True, related_name="worker_authorization_is_fitting"
    )
    worker_authorization_is_customer = models.ManyToManyField(
        "Worker", blank=True, related_name="worker_authorization_is_customer"
    )
    worker_authorization_is_worker = models.ManyToManyField(
        "Worker", blank=True, related_name="worker_authorization_is_worker"
    )
    worker_authorization_is_setting = models.ManyToManyField(
        "Worker", blank=True, related_name="worker_authorization_is_setting"
    )

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def apply_limits(self):
        try:
            package_type = self.workshop.package_histories.get(is_active=True)
            package_type_name = package_type.name
        except:
            package_type_name = Package.PackageType.DEMO
        finally:
            limits = Package.PACKAGE_LIMITS.get(package_type_name)
            for key, value in limits.items():
                setattr(self, key, value)
            self.save()


    