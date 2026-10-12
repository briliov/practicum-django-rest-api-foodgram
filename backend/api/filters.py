"""Filtering module providing custom query filters for API endpoints."""

import django_filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import filters
from entities.recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    """Filter set for parsing ingredient queries inside database indices."""

    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="istartswith",
    )

    class Meta:
        """Meta class for IngredientFilter."""

        model = Ingredient
        fields = ("name",)


class RecipeFilter(django_filters.FilterSet):
    """Filter set configuring query properties for Recipe endpoints."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart",
    )

    def filter_is_favorited(self, queryset, name, value):
        """Filter the queryset based on the item's favorited status."""
        assert self.request is not None
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(favorite_by__user=user)
        return queryset.exclude(favorite_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Filter the queryset based on items in the shopping cart."""
        assert self.request is not None
        user = self.request.user
        if user.is_anonymous:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(shoppingcart_by__user=user)
        return queryset.exclude(shoppingcart_by__user=user)

    class Meta:
        """Meta class for RecipeFilter."""

        model = Recipe
        fields = ("tags", "author")
