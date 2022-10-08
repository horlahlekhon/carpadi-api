from django.db.models import Q
from django_filters import rest_framework as filters

from src.models.models import CarProduct, CarTransmissionTypes, FuelTypes, CarTypes


class CarProductFilter(filters.FilterSet):
    selling_price = filters.NumericRangeFilter(field_name="selling_price")
    search = filters.CharFilter(field_name="car", method="search_field")
    year = filters.DateFromToRangeFilter(field_name="car__year")
    age = filters.NumericRangeFilter(field_name="car__age")
    transmission = filters.ChoiceFilter(
        field_name="car__transmission", lookup_expr="iexact", choices=CarTransmissionTypes.choices
    )
    fuel_type = filters.ChoiceFilter(field_name="car__fuel_type", lookup_expr="iexact", choices=FuelTypes.choices)
    car_type = filters.ChoiceFilter(field_name="car__car_type", lookup_expr="iexact", choices=CarTypes.choices)

    def search_field(self, queryset, name, value):
        return queryset.filter(
            Q(car__information__brand__model__icontains=value)
            | Q(car__information__manufacturer__icontains=value)
            | Q(car__information__fuel_type__icontains=value)
            | Q(car__information__car_type__icontains=value)
            | Q(car__vin__icontains=value)
            | Q(car__name__icontains=value)
            | Q(car__licence_plate__icontains=value)
        )

    class Meta:
        model = CarProduct
        fields = [
            "selling_price",
            "status",
        ]
