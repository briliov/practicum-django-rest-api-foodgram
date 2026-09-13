"""Serializers module providing data transformation pipelines for the API."""

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from .models import Following, Ingredient, Recipe, RecipeIngredient, Tag
from .utils import Base64ImageField

User = get_user_model()


class UsersCreateSerializer(serializers.ModelSerializer):
    """Serializer configuration for managing User registration flows."""

    class Meta:
        """Meta options mapping fields against the baseline User schema."""

        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password',)

        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [UniqueValidator(
                    queryset=User.objects.all(),
                    message="Пользователь с таким email уже существует.")]
            },
            'username': {
                'required': True,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message="Пользователь с таким username уже существует."
                    ),
                    RegexValidator(
                        regex=r'^[\w.@+-]+\Z',
                        message='Некорректное имя пользователя.'
                    )]
            },
            'password': {
                'required': True,
                'write_only': True
            },
            'first_name': {
                'required': True
            },
            'last_name': {
                'required': True
            },
        }

    def create(self, validated_data):
        """Creates a new database User object and handles password hashing."""
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer configuration for handling user thumbnail configurations."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Meta configurations specifying targets for User avatar mapping."""

        model = User
        fields = ('avatar',)


class UsersSerializer(UsersCreateSerializer, AvatarSerializer):
    """Comprehensive Serializer managing standard profile operations."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(UsersCreateSerializer.Meta, AvatarSerializer.Meta):
        """Meta inheritance layout combining fields from base components."""

        fields = (UsersCreateSerializer.Meta.fields
                  + AvatarSerializer.Meta.fields
                  + ('is_subscribed', ))

    def get_is_subscribed(self, obj) -> bool:
        """Determines active subscription status between profiles."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Following.objects.filter(user=request.user, following=obj
                                        ).exists()


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
    author = UsersSerializer(read_only=True)
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


class FollowingSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions and profile display.

    Includes user details, subscription status, author's recipes,
    and the total count of their recipes.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def validate(self, attrs):
        """Validate the subscription request.

        Prevents users from subscribing to themselves or duplicating
        an existing subscription.
        """
        request = self.context['request']
        author_id = self.context['view'].kwargs.get('pk')

        # Check if the user is trying to subscribe to themselves
        if request.user.id == int(author_id):
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')
        if Following.objects.filter(user=request.user,
                                    following_id=author_id).exists():
            raise serializers.ValidationError('Вы уже подписаны.')
        return attrs

    def create(self, validated_data):
        """Create a subscription between the current user and the author."""
        request = self.context['request']
        author_id = self.context['view'].kwargs.get('pk')
        Following.objects.create(user=request.user, following_id=author_id)
        return User.objects.get(id=author_id)

    def get_is_subscribed(self, obj) -> bool:
        """Check if the current user is subscribed to the author."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Following.objects.filter(
            user=request.user,
            following=obj
        ).exists()

    def get_recipes_count(self, obj) -> int:
        """Return the total number of recipes published by the author."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return 0
        return Recipe.objects.filter(author=obj).count()

    def get_recipes(self, obj):
        """Return the author's recipes with an optional limit constraint."""
        request = self.context.get('request')
        queryset = obj.recipes.all()

        if request:
            limit = request.query_params.get('recipes_limit')
            if limit and limit.isdigit():
                queryset = queryset[:int(limit)]
        serializer = ShortRecipeSerializer(queryset, many=True,
                                           context={'request': request})
        return serializer.data
