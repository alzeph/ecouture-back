from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class InternalNotification(models.Model):
    """
    Modèle de notification pour les utilisateurs.
    """

    class CategoryInternalNotification(models.TextChoices):
        WORKER_CREATION = 'WORKER_CREATION', 'Worker Creation'
        WORKER_UPDATE = 'WORKER_UPDATE', 'Worker Update'
        CUSTOMER_CREATION = 'CUSTOMER_CREATION', 'Customer Creation'
        CUSTOMER_UPDATE = 'CUSTOMER_UPDATE', 'Customer Update'
        CUSTOMER_DELETION = 'CUSTOMER_DELETION', 'Customer Deletion'
        ORDER_CREATION = 'ORDER_CREATION', 'Order Creation'
        ORDER_UPDATE = 'ORDER_UPDATE', 'Order Update'
        ORDER_DELETION = 'ORDER_DELETION', 'Order Deletion'
        ORDER_GROUP_CREATION = 'ORDER_GROUP_CREATION', 'Order Group Creation'
        ORDER_GROUP_UPDATE = 'ORDER_GROUP_UPDATE', 'Order Group Update'
        ORDER_GROUP_DELETION = 'ORDER_GROUP_DELETION', 'Order Group Deletion'
        FITTING_CREATION = 'FITTING_CREATION', 'Fitting Creation'
        FITTING_UPDATE = 'FITTING_UPDATE', 'Fitting Update'
        FITTING_DELETION = 'FITTING_DELETION', 'Fitting Deletion'
        WORKSHOP_CREATION = 'WORKSHOP_CREATION', 'Workshop Creation'
        WORKSHOP_UPDATE = 'WORKSHOP_UPDATE',   'Workshop Update'
        AUTHORISATION_ACCEPT = 'AUTHORISATION_ACCEPT', 'Authorisation Accept'
        AUTHORISATION_REJECT = 'AUTHORISATION_REJECT', 'Authorisation Reject'
        SETTING_CREATION = 'SETTING_CREATION', 'Setting Creation'
        SETTING_UPDATE = 'SETTING_UPDATE', 'Setting Update'

    class TypeInternalNotification(models.TextChoices):
        INFO = 'info', 'Information'
        WARNING = 'warning', 'Avertissement'
        ERROR = 'error', 'Erreur'
        SUCCESS = 'success', 'Succès'

    class ObjectContentInternalNotification(models.TextChoices):
        SETTING = 'Setting', 'Setting'
        WORKER = 'Worker', 'Worker'
        CUSTOMER = 'Customer', 'Customer'
        ORDER = 'Order', 'Order'
        ORDER_GROUP = 'OrderGroup', 'OrderGroup'
        FITTING = 'Fitting', 'Fitting'
        WORKSHOP = 'Workshop', 'Workshop'

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(
        max_length=50, choices=TypeInternalNotification.choices, default=TypeInternalNotification.INFO)
    read_at = models.DateTimeField(null=True, blank=True)
    category = models.CharField(
        max_length=50, choices=CategoryInternalNotification.choices, null=True, blank=True)
    object_content = models.CharField(
        max_length=50, choices=ObjectContentInternalNotification.choices, null=True, blank=True)
    object_pk = models.CharField(max_length=225, null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-createdAt']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
        verbose_name = 'Internal Notification'
        verbose_name_plural = 'Internal Notifications'


class ExternalNotification(models.Model):
    """
    Modèle de notification externe pour les utilisateurs.

    Utilisé pour les notifications envoyées par email ou SMS.
    """
    customer = models.ForeignKey(
        "workshop.CustomerWorkshop", on_delete=models.CASCADE, related_name='external_notifications')
    type = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification')
    ])
    scheduled_for = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
