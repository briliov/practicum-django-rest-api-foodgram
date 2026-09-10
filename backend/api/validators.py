"""Validators for the Foodgram API serializers.

This module contains custom validation functions used to verify input data
integrity before creating or updating recipes and related models.
"""

from rest_framework import serializers

from .models import Ingredient


def validate_recipe_ingredients(value):
    """Validate the list of ingredients provided for a recipe.

    Checks that the list is not empty, does not contain duplicate
    ingredients, and ensures all provided ingredient IDs exist
    in the database.
    """
    if not value:
        raise serializers.ValidationError(
            'Нужно выбрать хотя бы один ингредиент.',
        )

    # Extract ingredient IDs from the input list of dictionaries
    ingredient_ids = [
        item.get('id') for item in value if isinstance(item, dict)
    ]

    # Verify that there are no duplicate ingredients in the request
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError(
            'Ингредиенты не должны повторяться.'
        )

    # Check if all unique ingredient IDs exist in the database
    if Ingredient.objects.filter(
        id__in=ingredient_ids,
    ).count() != len(set(ingredient_ids)):
        raise serializers.ValidationError(
            'Указан несуществующий ингредиент.',
        )
