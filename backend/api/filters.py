from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(method='filter_in_cart')
    is_favorited = filters.BooleanFilter(method='filter_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'is_in_shopping_cart', 'is_favorited')

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return queryset.filter(favorites__user=user)
            return queryset.none()
        return queryset

    def filter_in_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            if user.is_authenticated:
                return queryset.filter(recipes_in_shopping_cart__user=user)
            return queryset.none()
        return queryset
