"""Serializers module providing data transformation pipelines for the API."""

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from entities.recipes.models import (Favorite, Ingredient, Recipe,
                                     RecipeIngredient, ShoppingCart, Tag,
                                     UserRecipe)

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer configuration for handling user thumbnail configurations."""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Meta configurations specifying targets for User avatar mapping."""

        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar')


class UserSubscribeSerializer(UserSerializer, AvatarSerializer):
    """Serializer with boolean parameter is_subscribed."""
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta, AvatarSerializer.Meta):
        """Meta class for UserSubscribeSerializer."""
        fields = (UserSerializer.Meta.fields + AvatarSerializer.Meta.fields
                  + ('is_subscribed',))


class TagSerializer(serializers.ModelSerializer):
    """Serializer representation mapping system categories and labels."""

    class Meta:
        """Meta mapping definitions tracking properties against Tag schema."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientsSerializer(serializers.ModelSerializer):
    """Serializer representation targeting stock database ingredients."""

    class Meta:
        """Meta descriptions linking fields against Ingredient model layout."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ReadIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class WriteIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Minified data serialization targeting subscription review panels."""

    class Meta:
        """Meta targets pinning minified records to Recipe models."""
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ReadRecipeSerializer(ShortRecipeSerializer):
    """Read serializer for Recipe model"""
    tags = TagSerializer(read_only=True, many=True)
    author = UserSubscribeSerializer(read_only=True)
    ingredients = ReadIngredientAmountSerializer(source='recipe_ingredients',
                                                 many=True,
                                                 read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta(ShortRecipeSerializer.Meta):
        """Meta class for ReadRecipeSerializer."""
        fields = ShortRecipeSerializer.Meta.fields + (
            'text',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for managing recipe creation, retrieval, and updates.

    Handles validation of nested tags and ingredients extracted from raw
    initial data, and dynamically calculates favorited and shopping cart
    statuses for the requesting user.
    """
    image = Base64ImageField(required=True)
    ingredients = WriteIngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'cooking_time',
            'image',
            'ingredients',
            'tags',
        )

    def validate(self, attrs):
        for field in ('tags', 'ingredients', 'image'):
            if field not in attrs:
                raise serializers.ValidationError(
                    {f'{field}': f'Передача поля {field} обязательна.'}
                )
            value = attrs.get(field)
            if not value or len(value) == 0:
                raise serializers.ValidationError(
                    {field: f'Поле {field} не может быть пустым.'}
                )
        return attrs

    def validate_tags(self, tags):
        ids = [tag.id for tag in tags]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Данный "tag" уже есть в рецепте!')
        return tags

    def validate_ingredients(self, ingredients):
        ids = [ingredient.get('ingredient').id for ingredient in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Данный ингредиент уже есть в рецепте!')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        """
        Helper method to bulk create through-model instances for the
        recipe-ingredient relationship.
        """
        recipe_ingredients = (
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get('ingredient'),
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """
        Create a new recipe instance, associate it with the current user,
        and set up M2M relations.
        """
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        """
        Update an existing recipe instance and completely refresh its
        tags and ingredient relations.
        """

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance = super().update(instance, validated_data)

        instance.tags.clear()
        instance.tags.set(tags_data)

        instance.recipe_ingredients.all().delete()
        self.create_ingredients(ingredients_data, instance)

        return instance

    def to_representation(self, instance):
        annotated_instance = self.context['view'].get_queryset(
        ).get(id=instance.id)
        serializer = ReadRecipeSerializer(annotated_instance,
                                          context=self.context)
        return serializer.data


class RecipeUserSubscribeSerializer(UserSubscribeSerializer):
    """
    Serializer for user with recipes, recipes_count and is_subscribed
    parameters.
    """
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSubscribeSerializer.Meta):
        fields = UserSubscribeSerializer.Meta.fields + (
            'recipes', 'recipes_count',)
