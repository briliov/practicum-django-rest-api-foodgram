"""Filtering module providing custom query filters for API endpoints."""

import django_filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import filters
from rest_framework.filters import SearchFilter

from entities.recipes.models import Recipe, Ingredient

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    """Filter set for parsing ingredient queries inside database indices."""
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        """Meta class for IngredientFilter."""
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """Filter set configuring query properties for Recipe endpoints."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorites_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset

    class Meta:
        """Meta class for RecipeFilter."""
        model = Recipe
        fields = ('tags', 'author')
