"""Serializers module providing data transformation pipelines for the API."""

from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from entities.recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from utils.constants import AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer configuration for handling user thumbnail configurations."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Meta configurations specifying targets for User avatar mapping."""

        model = User
        fields = ("avatar",)


class UserSerializer(DjoserUserSerializer):
    """Serializer for User model."""

    class Meta(DjoserUserSerializer.Meta):
        """Meta class for UserSerializer."""

        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
        )


class UserSubscribeSerializer(UserSerializer, AvatarSerializer):
    """Serializer with boolean parameter is_subscribed."""

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta, AvatarSerializer.Meta):
        """Meta class for UserSubscribeSerializer."""

        fields = UserSerializer.Meta.fields + ("is_subscribed",)


class TagSerializer(serializers.ModelSerializer):
    """Serializer representation mapping system categories and labels."""

    class Meta:
        """Meta mapping definitions tracking properties against Tag schema."""

        model = Tag
        fields = ("id", "name", "slug")


class IngredientsSerializer(serializers.ModelSerializer):
    """Serializer representation targeting stock database ingredients."""

    class Meta:
        """Meta descriptions linking fields against Ingredient model layout."""

        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class ReadIngredientAmountSerializer(serializers.ModelSerializer):
    """Display ingredient details with their quantities in a recipe."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit",
    )

    class Meta:
        """Meta class for ReadIngredientAmountSerializer."""

        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class WriteIngredientAmountSerializer(serializers.ModelSerializer):
    """Add or update ingredients and their quantities in a recipe."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN_VALUE,
        max_value=AMOUNT_MAX_VALUE,
    )

    class Meta:
        """Meta class for WriteIngredientAmountSerializer."""

        model = RecipeIngredient
        fields = ("id", "amount")


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Minified data serialization targeting subscription review panels."""

    class Meta:
        """Meta targets pinning minified records to Recipe models."""

        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class ReadRecipeSerializer(ShortRecipeSerializer):
    """Read serializer for Recipe model."""

    tags = TagSerializer(read_only=True, many=True)
    author = UserSubscribeSerializer(read_only=True)
    ingredients = ReadIngredientAmountSerializer(
        source="recipe_ingredients",
        many=True,
        read_only=True,
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta(ShortRecipeSerializer.Meta):
        """Meta class for ReadRecipeSerializer."""

        fields = ShortRecipeSerializer.Meta.fields + (
            "text",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        )


class WriteRecipeSerializer(serializers.ModelSerializer):
    """Serializer for managing recipe creation, retrieval, and updates.

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
        """Meta class for ReadRecipeSerializer."""

        model = Recipe
        fields = (
            "name",
            "text",
            "cooking_time",
            "image",
            "ingredients",
            "tags",
        )

    def validate(self, attrs):
        """Validate all data."""
        for field in ("tags", "ingredients"):
            if field not in attrs:
                raise serializers.ValidationError(
                    {f"{field}": f"Передача поля {field} обязательна."},
                )
            value = attrs.get(field)
            if not value:
                raise serializers.ValidationError(
                    {field: f"Поле {field} не может быть пустым."},
                )
        return attrs

    def validate_image(self, value):
        """Проверка поля image, если оно передано в запросе."""
        if not value:
            raise serializers.ValidationError(
                "Поле image не может быть пустым.",
            )
        return value

    def validate_tags(self, tags):
        """Validate all tags."""
        ids = [tag.id for tag in tags]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Данный "tag" уже есть в рецепте!',
            )
        return tags

    def validate_ingredients(self, ingredients):
        """Validate all ingredients."""
        ids = [ingredient.get("ingredient").id for ingredient in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Данный ингредиент уже есть в рецепте!",
            )
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        """Auxiliary method for creating ingredients."""
        recipe_ingredients = (
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient.get("ingredient"),
                amount=ingredient.get("amount"),
            )
            for ingredient in ingredients
        )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        """Return created recipe."""
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Return updated recipe."""
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")

        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)

        instance.recipe_ingredients.all().delete()
        self.create_ingredients(ingredients_data, instance)

        return instance

    def to_representation(self, instance):  # type: ignore
        """Return serialized recipe data."""
        annotated_instance = (
            self.context["view"].get_queryset().get(id=instance.id)
        )
        serializer = ReadRecipeSerializer(
            annotated_instance,
            context=self.context,
        )
        return serializer.data


class RecipeUserSubscribeSerializer(UserSubscribeSerializer):
    """Represent user with recipes, count, and subscription status."""

    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSubscribeSerializer.Meta):
        """Meta class for RecipeUserSubscribeSerializer."""

        fields = UserSubscribeSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )
