"""Views for API users application."""

from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, mixins, filters, permissions
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import (UsersSerializer, IngredientsSerializer,
                          TagSerializer, RecipeSerializer, AvatarSerializer,
                          UsersCreateSerializer)
from .models import Ingredient, Tag, Recipe, Following

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

    def get_serializer_class(self):
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
