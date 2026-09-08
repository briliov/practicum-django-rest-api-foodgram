from django_filters import rest_framework as django_filters

from .models import Ingredient, Tag, Recipe, ShoppingCart, Favorite 


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'is_in_shopping_cart', 'is_favorited')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if str(value) in ('1', '1.0', 'True', 'true'):
            user_recipes_ids = ShoppingCart.objects.filter(
                user=self.request.user).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=user_recipes_ids)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if str(value) in ('1', '1.0', 'True', 'true'):
            user_recipes_ids = Favorite.objects.filter(
                user=self.request.user).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=user_recipes_ids)
        return queryset