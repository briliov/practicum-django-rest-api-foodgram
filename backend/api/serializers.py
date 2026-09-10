"""Serializers module providing data transformation pipelines for the API."""

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from .models import Following, Ingredient, Recipe, RecipeIngredient, Tag
from .utils import Base64ImageField
from .validators import validate_recipe_ingredients

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


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    """Write-only mapping payload tracking quantitative index properties."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Meta mapping targets binding configurations against Recipe
        bounds."""

        model = Recipe
        fields = ('id', 'amount')


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


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Dynamic operational serializer managing mutation tasks for Recipes."""

    ingredients = IngredientAmountWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField(required=True)
    author = UsersSerializer(
        required=False,
        default=serializers.CurrentUserDefault()
    )
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        """Meta schema tracking writing constraints against Recipe
        structures."""

        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, attrs):
        """Verifies integrity maps inside active multi-choice datasets."""

        for attr_name in ['ingredients', 'tags']:
            attr_name = attrs.get(attr_name)
            if attr_name is None or len(attr_name) < 1:
                raise serializers.ValidationError(
                    {'ingredients': 'Добавьте хотя бы один ингредиент'}
                )
        return attrs

    def validate_ingredients(self, value):
        """Validates nested ingredient blocks to reject empty indices."""

        if not value or len(value) < 1:
            raise ValidationError('Добавьте хотя бы один ингредиент')
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate_tags(self, value):
        """Validates incoming structural arrays to block duplicated labels."""

        tags = [tag.id for tag in value]
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторяться.')
        return value

    def _save_ingredients(self, recipe, ingredients_data):
        """Optimized insertion utility packing components via a single
        query."""

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredients=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    def create(self, validated_data):
        """Instantiates Recipe entities and manages structural contexts."""

        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        author = validated_data.pop(
            'author', self.context.get('request').user)  # type: ignore
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._save_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        """Safely mutates existing Recipe attributes and overrides
        relations."""

        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipeingredient_set.all().delete()
        self._save_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):  # type: ignore
        """Implements Split pattern to return nested GET representations."""

        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer configuration rendering complete detailed Recipe objects."""

    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(
        required=False,
        default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientsSerializer(
        many=True, validators=[validate_recipe_ingredients])
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)

    class Meta:
        """Meta descriptions binding full view components to Recipe records."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj) -> bool:
        """Determines if the active recipe exists inside user bookmark
        indices."""

        request = self.context.get('request')
        # Continuation of the previous serializer
        # (shopping cart check method)
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj) -> bool:
        """Check if the recipe is added to the user's shopping cart."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=obj).exists()


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
