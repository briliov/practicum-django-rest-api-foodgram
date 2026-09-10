"""Filtering module providing custom query filters for API endpoints."""

import django_filters

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class IngredientFilter(django_filters.FilterSet):
    """Filter set for parsing ingredient queries inside database indices."""
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        """Meta options mapping properties against the configuration."""

        model = Ingredient
        fields = ['name']


class RecipeFilter(django_filters.FilterSet):
    """Filter set configuring query properties for Recipe endpoints."""

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
        """Meta options mapping properties against the configuration."""

        model = Recipe
        fields = ('author', 'is_in_shopping_cart', 'is_favorited')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Filters recipes based on active instances inside the layout."""

        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if str(value) in ('1', '1.0', 'True', 'true'):
            user_recipes_ids = ShoppingCart.objects.filter(
                user=self.request.user).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=user_recipes_ids)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Filters recipes based on user bookmark lists."""

        if not self.request or not self.request.user:
            return queryset.none()

        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if str(value) in ('1', '1.0', 'True', 'true'):
            user_recipes_ids = Favorite.objects.filter(
                user=self.request.user).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=user_recipes_ids)
        return queryset
