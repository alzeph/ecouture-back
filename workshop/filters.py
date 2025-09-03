import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q
from workshop.models import (
    Worker, CustomerWorkshop, OrderWorkshop,
)


class WorkerFilterSet(filters.FilterSet):
    class Meta:
        model = Worker
        # ajoute les champs filtrables ici
        fields = ["is_active", "is_allowed"]


class NameInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass

class CustomerWorkshopFilterSet(django_filters.FilterSet):
    name = NameInFilter(method="search", label="Recherche globale (multi)")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = CustomerWorkshop
        fields = ["name", "genre", "is_active"]

    def search(self, queryset, name, values):
        q_objects = Q()
        for value in values:
            q_objects |= (
                Q(last_name__icontains=value) |
                Q(first_name__icontains=value) |
                Q(nickname__icontains=value)
            )
        return queryset.filter(q_objects)


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """Permet d'accepter plusieurs entiers (?id=1&id=2)."""
    def filter(self, qs, value):
        if not value:
            return qs
        # Ici, value peut être une liste ["24", "23", "22"]
        if isinstance(value, (list, tuple)):
            return qs.filter(**{f"{self.field_name}__{self.lookup_expr}": value})
        return super().filter(qs, value)

class OrderWorkshopFilterSet(filters.FilterSet):
    # Filtres par choix
    gender = filters.ChoiceFilter(choices=OrderWorkshop.Gender.choices)
    type_of_clothing = filters.MultipleChoiceFilter(
        field_name="typeOfClothing",
        choices=OrderWorkshop.TypeOfClothing.choices,
    )
    payment_status = filters.ChoiceFilter(choices=OrderWorkshop.PaymentStatus.choices)
    status = filters.MultipleChoiceFilter(choices=OrderWorkshop.OrderStatus.choices)

    # Filtres FK (⚡ maintenant multiple)
    customer = NumberInFilter(field_name="customer_id", lookup_expr="in")
    worker = NumberInFilter(field_name="worker_id", lookup_expr="in")

    # Filtres booléens
    is_urgent = filters.BooleanFilter()

    # Filtres sur la période de création
    created_after = filters.DateTimeFilter(field_name="createdAt", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="createdAt", lookup_expr="lte")
    
    delivery_after = filters.DateTimeFilter(field_name="promised_delivery_date", lookup_expr="gte")
    delivery_before = filters.DateTimeFilter(field_name="promised_delivery_date", lookup_expr="lte")

    # Recherche textuelle globale
    q = filters.CharFilter(method="global_search")

    def global_search(self, queryset, name, value):
        return queryset.filter(
            Q(description__icontains=value)
            | Q(description_of_model__icontains=value)
            | Q(description_of_fabric__icontains=value)
        )

    class Meta:
        model = OrderWorkshop
        fields = [
            "gender",
            "type_of_clothing",
            "payment_status",
            "status",
            "customer",
            "worker",
            "is_urgent",
            "created_after",
            "created_before",
        ]
        
            
