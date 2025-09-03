from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from haberdashery.mixins import HaberdasheryMixin

@method_decorator(csrf_exempt, name='dispatch')
class HaberdasheryViewSet(HaberdasheryMixin, GenericViewSet):
    pass