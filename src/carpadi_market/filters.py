from django_filters import rest_framework as filters

from src.models.models import CarProduct


class CarProductFilter(filters.FilterSet):
    selling_price = filters.NumericRangeFilter(field_name="selling_price")

    class Meta:
        model = CarProduct
        fields = ["selling_price"]
