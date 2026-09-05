from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError

from .utils import Base64ImageField
from .models import Ingredient, Tag, Recipe, RecipeIngredient, Following
from .validators import validate_recipe_ingredients

User = get_user_model()


class UsersCreateSerializer(serializers.ModelSerializer):
    """Serializer for create Users."""
    class Meta:
        """Meta class for create users."""
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
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    """AvatarSerializer for User"""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Meta class of AvatarSerializer."""
        model = User
        fields = ('avatar',)


class UsersSerializer(UsersCreateSerializer, AvatarSerializer):
    """Serializer for Users."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(UsersCreateSerializer.Meta, AvatarSerializer.Meta):
        """Meta class of UsersSerializer."""
        fields = (UsersCreateSerializer.Meta.fields
                  + AvatarSerializer.Meta.fields
                  + ('is_subscribed', ))

    def get_is_subscribed(self, obj) -> bool:
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Following.objects.filter(user=request.user, following=obj
                                        ).exists()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tags"""

    class Meta:
        """Meta class of TagsSerializer."""
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Serializer for Ingredients"""

    class Meta:
        """Meta class of IngredientsSerializer."""
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
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
        for attr_name in ['ingredients', 'tags']:
            attr_name = attrs.get(attr_name)
            if attr_name is None or len(attr_name) < 1:
                raise serializers.ValidationError(
                    {'ingredients': 'Добавьте хотя бы один ингредиент'}
                )
        return attrs

    def validate_ingredients(self, value):
        if not value or len(value) < 1:
            raise ValidationError('Добавьте хотя бы один ингредиент')
        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate_tags(self, value):
        tags = [tag.id for tag in value]
        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторяться.')
        return value

    def _save_ingredients(self, recipe, ingredients_data):
        """Оптимизированное сохранение связей через один SQL-запрос."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredients=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        author = validated_data.pop('author',
                                    self.context.get('request').user)
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._save_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        """Безопасное и полное обновление рецепта."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipeingredient_set.all().delete()
        self._save_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Паттерн Read/Write split: отдаем клиенту развернутый GET-формат."""
        return RecipeSerializer(instance, context=self.context).data


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for User."""
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
        """Meta class of UsersSerializer."""
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
            'cooking_time'
        )

    def get_is_favorited(self, obj) -> bool:
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj) -> bool:
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.shopping_cart.filter(recipe=obj).exists()

