from django.db.models.signals import post_save
from django.dispatch import receiver

from workshop.models import  Setting
from haberdashery.models import Haberdashery

@receiver(post_save, sender=Setting, dispatch_uid="workshop_create_haberdashery")
def create_haberdashery(sender, instance: Setting, created, **kwargs):
    if created:
        workshop = instance.workshop
        end_date = instance.end_date
        try:
            workshop.haberdashery
        except:
            Haberdashery.objects.create(workshop=workshop, end_date=end_date)



