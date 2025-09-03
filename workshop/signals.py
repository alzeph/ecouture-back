from django.db.models.signals import post_save
from django.dispatch import receiver
from workshop.models import (
    Setting, Workshop, Worker,  PackageHistory, Package
)

from users.models import GROUPS
from users.utils import get_or_create_group

from django.utils import timezone
from datetime import timedelta


@receiver(post_save, sender=Workshop, dispatch_uid="workshop_create_setting")
def create_workshop(sender, instance: Workshop, created, **kwargs):
    if created:
        package = Package.objects.get(name=Package.PackageType.DEMO)
        PackageHistory.objects.create(
            workshop=instance,
            name=package.name,
            price=package.price,
            start_date=timezone.now().date(),
            end_date=timezone.now().date()+package.duration,
        )
    return

@receiver(post_save, sender=PackageHistory, dispatch_uid="setting_create_package_history")
def create_package_history(sender, instance: PackageHistory, created, **kwargs):
    if created:
       setting, _ = Setting.objects.get_or_create(workshop=instance.workshop)
       setting.apply_limits()
    
        

@receiver(post_save, sender=Worker, dispatch_uid="worker_create_package_history")
def create_worker(sender, instance: Worker, created, **kwargs):
    if created:
        group_worker = get_or_create_group(GROUPS["WORKERS"])
        instance.user.groups.add(group_worker)
