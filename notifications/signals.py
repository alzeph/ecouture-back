from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from workshop.models import (
    OrderWorkshop, OrderWorkshopGroup, CustomerWorkshop,
    Setting, Workshop, Worker, Fitting
)
from notifications.models import InternalNotification, ExternalNotification


def create_internal_notification(user, category, type, title, message, object_content=None, object_pk=None):
    InternalNotification.objects.create(
        user=user,
        category=category,
        type=type,
        title=title,
        message=message,
        object_content=object_content,
        object_pk=object_pk
    )


@receiver(post_save, sender=Workshop, dispatch_uid="workshop_create_new")
def create_workshop(sender, instance: Workshop, created, **kwargs):
    if created:
        for owner in instance.get_owners():
            create_internal_notification(
                user=owner.user,
                category=InternalNotification.CategoryInternalNotification.WORKSHOP_CREATION,
                type=InternalNotification.TypeInternalNotification.INFO,
                title='Atelier créé',
                message=f"Votre atelier '{instance.name}' a été créé avec succès.",
                object_content=InternalNotification.ObjectContentInternalNotification.WORKSHOP,
                object_pk=instance.pk
            )


@receiver(post_save, sender=OrderWorkshop, dispatch_uid="order_workshop_create_notification")
def create_order_workshop(sender, instance: OrderWorkshop, created, **kwargs):
    owners = instance.worker.workshop.get_owners()
    if created:
        create_internal_notification(
            user=instance.worker.user,
            category=InternalNotification.CategoryInternalNotification.ORDER_CREATION,
            type=InternalNotification.TypeInternalNotification.INFO,
            title='Nouvelle commande',
            message=f"Une nouvelle commande '{instance.number}' a été créée pour vous.",
            object_content=InternalNotification.ObjectContentInternalNotification.ORDER,
            object_pk=instance.pk
        )
        ExternalNotification.objects.create(
            customer=instance.customer,
            type='email',
            title='Commande créée',
            message=f"Votre commande '{instance.number}' a été créée avec succès. Veuillez vérifier les détails de votre commande."
        )
    else:
        if instance.is_deleted:
            create_internal_notification(
                user=instance.worker.user,
                category=InternalNotification.CategoryInternalNotification.ORDER_DELETION,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Commande annulée',
                message=f"La commande '{instance.number}' a été annulée."
            )
        if instance.status == OrderWorkshop.OrderStatus.COMPLETED:
            for user in [instance.worker.user] + [o.user for o in owners]:
                create_internal_notification(
                    user=user,
                    category=InternalNotification.CategoryInternalNotification.ORDER_UPDATE,
                    type=InternalNotification.TypeInternalNotification.SUCCESS,
                    title='Commande terminée',
                    message=f"La commande '{instance.number}' a été marquée comme terminée.",
                    object_content=InternalNotification.ObjectContentInternalNotification.ORDER,
                    object_pk=instance.pk
                )
        if instance.status == OrderWorkshop.OrderStatus.IN_PROGRESS:
            for user in [instance.worker.user] + [o.user for o in owners]:
                create_internal_notification(
                    user=user,
                    category=InternalNotification.CategoryInternalNotification.ORDER_UPDATE,
                    type=InternalNotification.TypeInternalNotification.INFO,
                    title='Commande en cours',
                    message=f"La commande '{instance.number}' est en cours de traitement.",
                    object_content=InternalNotification.ObjectContentInternalNotification.ORDER,
                    object_pk=instance.pk
                )
        if instance.payment_status == OrderWorkshop.PaymentStatus.PAID:
            for user in [instance.worker.user] + [o.user for o in owners]:
                create_internal_notification(
                    user=user,
                    category=InternalNotification.CategoryInternalNotification.ORDER_UPDATE,
                    type=InternalNotification.TypeInternalNotification.SUCCESS,
                    title='Commande payée',
                    message=f"La commande '{instance.number}' a été marquée comme payée.",
                    object_content=InternalNotification.ObjectContentInternalNotification.ORDER,
                    object_pk=instance.pk
                )


@receiver(post_save, sender=OrderWorkshopGroup, dispatch_uid="order_workshop_group_create_notification")
def create_order_workshop_group(sender, instance: OrderWorkshopGroup, created, **kwargs):
    if created:
        workers = Worker.objects.filter(pk__in=instance.orders.values_list('worker', flat=True).distinct())
        for worker in workers:
            create_internal_notification(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.ORDER_GROUP_CREATION,
                type=InternalNotification.TypeInternalNotification.INFO,
                title='Groupe de commandes créé',
                message=f"Un nouveau groupe de commandes '{instance.number}' a été créé pour vous.",
                object_content=InternalNotification.ObjectContentInternalNotification.ORDER_GROUP,
                object_pk=instance.pk
            )


@receiver(post_save, sender=CustomerWorkshop, dispatch_uid="customer_workshop_create_notification")
def create_customer_workshop(sender, instance: CustomerWorkshop, created, **kwargs):
    if created:
        workers = instance.workshop.workers.all()
        for worker in workers:
            create_internal_notification(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.CUSTOMER_CREATION,
                type=InternalNotification.TypeInternalNotification.INFO,
                title='Nouveau client',
                message=f"Un nouveau client '{instance.first_name} {instance.last_name}' a été ajouté à votre atelier (surnom: '{instance.nickname}').",
                object_content=InternalNotification.ObjectContentInternalNotification.CUSTOMER,
                object_pk=instance.pk
            )
            
        # ExternalNotification.objects.create(
        #     customer=instance,
        #     type='email',
        #     title='Bienvenue dans l'atelier',
        #     message=f"Bonjour {instance.first_name},\n\nBienvenue dans l'atelier '{instance.workshop.name}'. Nous sommes ravis de vous avoir avec nous."
        # )


@receiver(post_save, sender=Fitting, dispatch_uid="fitting_create_notification")
def create_fitting(sender, instance: Fitting, created, **kwargs):
    worker = instance.order.worker
    owners = worker.workshop.get_owners()
    if created:
        for user in [worker.user, *[o.user for o in owners]]:
            create_internal_notification(
                user=user,
                category=InternalNotification.CategoryInternalNotification.FITTING_CREATION,
                type=InternalNotification.TypeInternalNotification.INFO,
                title='Nouvel essayage',
                message=f"Un nouvel essayage a été planifié pour la commande '{instance.order.number}'.",
                object_content=InternalNotification.ObjectContentInternalNotification.FITTING,
                object_pk=instance.pk
            )
        ExternalNotification.objects.create(
            customer=instance.order.customer,
            type='email',
            title='Essayage planifié',
            message=f"Un essayage a été planifié pour votre commande '{instance.order.number}'. Veuillez vérifier les détails de l'essayage."
        )


# Les signaux m2m_changed sont corrigés avec pk_set utilisé correctement et typos corrigées


@receiver(m2m_changed, sender=Setting.worker_authorization_is_customer, dispatch_uid="setting_create_notification_m2m")
def create_setting_notification_m2m_worker_authorization_is_customer(sender, instance: Setting, action, pk_set, **kwargs):
    Workers = instance.workshop.workers.filter(pk__in='pk_set')
    if action == "post_add":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_ACCEPT,
                type=InternalNotification.TypeInternalNotification.SUCCESS,
                title='Autorisation de client',
                message=f"Vous avez été autorisé à voir, ajouter , modifier la liste des clients de l'atelier '{instance.workshop.name}'.",

            )
    if action == "post_remove":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_REJECT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Retrait de l\'autorisation de client',
                message=f"Vous n'êtes plus autorisé à voir, ajouter ou modifier la liste des clients de l'atelier '{instance.workshop.name}'."
            )


@receiver(m2m_changed, sender=Setting.worker_authorization_is_order, dispatch_uid="setting_create_notification_m2m_order")
def create_setting_notification_m2m_worker_authorization_is_order(sender, instance: Setting, action, pk_set, **kwargs):
    Workers = instance.workshop.workers.filter(pk__in='pk_set')
    if action == "post_add":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_ACCEPT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Autorisation de commande',
                message=f"Vous avez été autorisé ajouter, modifier les commandes de l'atelier '{instance.workshop.name}'."
            )

    if action == "post_remove":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_REJECT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Retrait de l\'autorisation de commande',
                message=f"Vous n'êtes plus autorisé à ajouter ou modifier les commandes de l'atelier '{instance.workshop.name}'."
            )


@receiver(m2m_changed, sender=Setting.worker_authorization_is_fitting, dispatch_uid="setting_create_notification_m2m_fitting")
def create_setting_notification_m2m_worker_authorization_is_fitting(sender, instance: Setting, action, pk_set, **kwargs):
    Workers = instance.workshop.workers.filter(pk__in='pk_set')
    if action == "post_add":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                tcategory=InternalNotification.CategoryInternalNotification.AUTHORISATION_ACCEPT,
                type=InternalNotification.TypeInternalNotification.SUCCESS,
                title='Autorisation d\'essayage',
                message=f"Vous avez été autorisé à ajouter, modifier les essayages de l'atelier '{instance.workshop.name}'."
            )
    if action == "post_remove":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_REJECT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Retrait de l\'autorisation d\'essayage',
                message=f"Vous n'êtes plus autorisé à ajouter ou modifier les essayages de l'atelier '{instance.workshop.name}'."
            )


@receiver(m2m_changed, sender=Setting.worker_authorization_is_worker, dispatch_uid="setting_create_notification_m2m_worker")
def create_setting_notification_m2m_worker_authorization_is_worker(sender, instance: Setting, action, pk_set, **kwargs):
    Workers = instance.workshop.workers.filter(pk__in='pk_set')
    if action == "post_add":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_ACCEPT,
                type=InternalNotification.TypeInternalNotification.SUCCESS,
                title='Autorisation de travailleur',
                message=f"Vous avez été autorisé à ajouter, modifier les travailleurs de l'atelier '{instance.workshop.name}'."
            )
    if action == "post_remove":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_REJECT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Retrait de l\'autorisation de travailleur',
                message=f"Vous n'êtes plus autorisé à ajouter ou modifier les travailleurs de l'atelier '{instance.workshop.name}'."
            )


@receiver(m2m_changed, sender=Setting.worker_authorization_is_setting, dispatch_uid="setting_create_notification_m2m_setting")
def create_setting_notification_m2m_worker_authorization_is_setting(sender, instance: Setting, action, pk_set, **kwargs):
    Workers = instance.workshop.workers.filter(pk__in='pk_set')
    if action == "post_add":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_ACCEPT,
                type=InternalNotification.TypeInternalNotification.SUCCESS,
                title='Autorisation de paramètres',
                message=f"Vous avez été autorisé à modifier les paramètres de l'atelier '{instance.workshop.name}'."
            )
    if action == "post_remove":
        for worker in Workers:
            InternalNotification.objects.create(
                user=worker.user,
                category=InternalNotification.CategoryInternalNotification.AUTHORISATION_REJECT,
                type=InternalNotification.TypeInternalNotification.ERROR,
                title='Retrait de l\'autorisation de paramètres',
                message=f"Vous n'êtes plus autorisé à modifier les paramètres de l'atelier '{instance.workshop.name}'."
            )
