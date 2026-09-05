from rest_framework import serializers
from .models import Ingredient


def validate_recipe_ingredients(value):
    if not value:
        raise serializers.ValidationError('Нужно выбрать хотя бы один '
                                          'ингредиент.')

    ingredient_ids = [item.get('id') for item in value if isinstance(item,
                                                                     dict)]

    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError('Ингредиенты не должны повторяться.')

    if Ingredient.objects.filter(id__in=ingredient_ids
                                 ).count() != len(set(ingredient_ids)):
        raise serializers.ValidationError('Указан несуществующий ингредиент.')
