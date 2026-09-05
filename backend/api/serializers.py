from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .utils import Base64ImageField
from .models import Ingredient, Tag, Recipe, ShoppingCart, Following

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
