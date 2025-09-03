import random
from decimal import Decimal, ROUND_DOWN
from django.contrib import admin
from workshop.models import (
     Worker, CustomerWorkshop, OrderWorkshop, Workshop,
    OrderWorkshopGroup, OrderWorkshopGroup, Fitting, Setting,Package
)


admin.site.register(Worker)
admin.site.register(CustomerWorkshop)
admin.site.register(Workshop)
admin.site.register(OrderWorkshopGroup)
admin.site.register(Fitting)
admin.site.register(Setting)
admin.site.register(Package)


@admin.action(description="Changer le statut de façon aléatoire")
def randomize_status(modeladmin, request, queryset):
    STATUSES = [choice[0] for choice in OrderWorkshop.OrderStatus.choices]
    for order in queryset:
        order.status = random.choice(STATUSES)
        order.save()


@admin.action(description="Changer le statut de paiement de façon aléatoire")
def randomize_payment_status(modeladmin, request, queryset):
    for order in queryset:
        if order.amount is not None and order.amount > 0:
            # Génère un float entre 0 et amount
            raw_value = random.uniform(0, float(order.amount))
            # Convertit en Decimal avec 2 décimales
            value = Decimal(str(raw_value)).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN)
            order.down_payment = value

            # Met à jour le statut de paiement
            if order.down_payment == 0:
                order.payment_status = order.PaymentStatus.PENDING
            elif order.down_payment < order.amount:
                order.payment_status = order.PaymentStatus.PARTIAL
            else:
                order.payment_status = order.PaymentStatus.PAID

            order.save()

import random
from datetime import datetime, timedelta, timezone

@admin.action(description="Assigner une date aléatoire entre 1er juillet et 31 août")
def assign_random_dates(modeladmin, request, queryset):
    start_date = datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 10, 30, 23, 59, 59, tzinfo=timezone.utc)
    delta = end_date - start_date

    for obj in queryset:
        random_seconds = random.randint(0, int(delta.total_seconds()))
        obj.promised_delivery_date  = start_date + timedelta(seconds=random_seconds)
        obj.createdAt = start_date + timedelta(seconds=random_seconds)
        obj.updatedAt = obj.createdAt  # optionnel si tu veux les aligner
        obj.save(update_fields=["createdAt", "updatedAt"])


@admin.register(OrderWorkshop)
class OrderWorkshopAdmin(admin.ModelAdmin):
    list_display = ('pk', 'customer', 'worker', 'status',
                    'payment_status', 'createdAt', 'updatedAt')
    list_filter = ('status', 'payment_status',
                   'customer', 'worker', 'createdAt')
    search_fields = ('customer__name', 'worker__name')
    readonly_fields = ('createdAt', 'updatedAt')
    actions = [randomize_status, randomize_payment_status, assign_random_dates]

    # Si tu as des fichiers à uploader (ImageField/FileField), ça les gère automatiquement
