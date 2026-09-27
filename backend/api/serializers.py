"""Serializers module providing data transformation pipelines for the API."""

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer

from entities.recipes.models import (Ingredient, Recipe,
                                     RecipeIngredient, Tag)
from entities.users.models import Following
from rest_framework.permissions import IsAuthenticatedOrReadOnly

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


class UserSubscribeSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = ('is_subscribed',) + UserSerializer.Meta.fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if (request is None) or request.user.is_anonymous:
            return False
        return request.user.subscriptions.filter(user=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Serializer representation mapping system categories and labels."""

    class Meta:
        """Meta mapping definitions tracking properties against Tag schema."""

        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Serializer representation targeting stock database ingredients."""

    class Meta:
        """Meta descriptions linking fields against Ingredient model layout."""

        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Minified data serialization targeting subscription review panels."""

    class Meta:
        """Meta targets pinning minified records to Recipe models."""

        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=RecipeIngredient.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for managing recipe creation, retrieval, and updates.

    Handles validation of nested tags and ingredients extracted from raw
    initial data, and dynamically calculates favorited and shopping cart
    statuses for the requesting user.
    """
    image = Base64ImageField()
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        """
        Determine if the current authenticated user has favorited this recipe.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites_by__user=user,
                                     id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Determine if the current authenticated user has added this recipe to
        their shopping cart.
        """
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(shopping_carts__user=user,
                                     id=obj.id).exists()

    def validate_cooking_time(self, value):
        """
        Validate that the provided cooking time is strictly greater than
        0 minutes.
        """
        if value <= 0:
            raise serializers.ValidationError(
                'Время приготовления должно быть больше 0 минут!'
            )
        return value

    def validate(self, attrs):
        """
        Perform complex validation on incoming recipe data.

        Ensures that ingredients and tags are provided, exist in the database,
        are mutually unique within the request, and have positive amounts.
        """
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингридиент для рецепта'})
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError({
                    'ingredients':
                        f'Ингредиент с id {ingredient_id} не существует!'
                })
            ingredient = Ingredient.objects.get(id=ingredient_id)
            if ingredient in ingredient_list:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты должны быть уникальными'
                })
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 0')
                })
        attrs['ingredients'] = ingredients
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужен хоть один тег для рецепта'})
        tags_list = []
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError({
                    'tags': f'Тег с id {tag_id} не существует!'
                })
            if tag_id in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Теги должны быть уникальными'
                })
            tags_list.append(tag_id)
        return attrs

    def create_ingredients(self, ingredients, recipe):
        """
        Helper method to bulk create through-model instances for the
        recipe-ingredient relationship.
        """
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        """
        Create a new recipe instance, associate it with the current user,
        and set up M2M relations.
        """
        ingredients_data = validated_data.pop('ingredients')
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        tags_data = self.initial_data.get('tags')
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Update an existing recipe instance and completely refresh its
        tags and ingredient relations.
        """
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        RecipeIngredient.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        instance.save()
        return instance
