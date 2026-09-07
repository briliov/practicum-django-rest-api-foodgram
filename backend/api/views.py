"""Views for API users application."""

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import (UsersSerializer, IngredientsSerializer,
                          TagSerializer, RecipeSerializer, AvatarSerializer,
                          UsersCreateSerializer, RecipeWriteSerializer,
                          ShortRecipeSerializer)
from .models import (Ingredient, Tag, Recipe, Favorite, ShoppingCart,
                     RecipeIngredient)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .utils import generate_shopping_cart_pdf

User = get_user_model()


@extend_schema_view(
    list=extend_schema(summary='Список пользователей'),
    create=extend_schema(summary='Регистрация пользователя'),
    retrieve=extend_schema(summary='Профиль пользователя'),
)
@extend_schema(tags=['Пользователи'])
class UsersViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    """Endpoint for Users."""
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):  # type: ignore
        if self.action == 'create':
            return UsersCreateSerializer
        return super().get_serializer_class()

    @extend_schema(summary='Текущий пользователь')
    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=None)
    def current_user(self, request):
        return Response(self.get_serializer(request.user).data,
                        status=status.HTTP_200_OK)

    @extend_schema(summary='Добавление аватара')
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=AvatarSerializer)
    def user_image(self, request):
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=True)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'detail': 'У вас нет аватара для удаления.'},
                            status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary='Изменение пароля')
    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[permissions.IsAuthenticated],)
    def change_user_password(self, request):
        if not request.user.check_password(request.data['current_password']):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(request.data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(summary='Список ингредиентов'),
    retrieve=extend_schema(summary='Получение ингредиента')
)
@extend_schema(tags=['Ингредиенты'])
class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint for Ingredients."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    ordering_fields = ['name',]


@extend_schema_view(
    list=extend_schema(summary='Список тегов'),
    retrieve=extend_schema(summary='Получение тега',)
)
@extend_schema(tags=['Теги'])
class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint for Tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


@extend_schema_view(
    list=extend_schema(summary='Список рецептов'),
    create=extend_schema(summary='Создание рецепта'),
    retrieve=extend_schema(summary='Получение рецепта'),
    partial_update=extend_schema(summary='Обновление рецепта'),
)
@extend_schema(tags=['Рецепты'])
class RecipeViewSet(viewsets.ModelViewSet):
    """Endpoint for Recipes."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthorOrReadOnly,]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter

    def get_serializer_class(self):  # type: ignore
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeWriteSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if self.get_object():
            return Response(
                {'short-link': request.build_absolute_uri(f'/s/{pk}')},
                status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            serializer_class=ShortRecipeSerializer)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if not Favorite.objects.get_or_create(user=user, recipe=recipe)[1]:
                return Response({'errors': 'Этот рецепт уже в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favorite.objects.filter(user=user, recipe=recipe
                                           ).delete()[0]:
                return Response({'errors': 'Рецепта не было в избранном.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post', 'delete'],
            url_path='shopping_cart', serializer_class=ShortRecipeSerializer)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if not ShoppingCart.objects.get_or_create(user=user,
                                                      recipe=recipe)[1]:
                return Response({'errors': 'Этот рецепт уже в корзине.'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(user=user, recipe=recipe
                                               ).delete()[0]:
                return Response({'errors': 'Рецепта не было в корзине.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shoping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values('ingredients__name', 'ingredients__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredients__name')
        )

        pdf_buffer = generate_shopping_cart_pdf(ingredients)
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename='shopping_cart.pdf'
        )
