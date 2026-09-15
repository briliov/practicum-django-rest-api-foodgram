"""Views for API users and recipe application.

This module provides ViewSets for handling User profiles, Follow relationships,
Ingredients, Tags, and Recipe interactions (including Favorites and Shopping
Cart).
"""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import (Favorite, Following, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, FollowingSerializer,
                          IngredientsSerializer, RecipeSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UsersCreateSerializer, UsersSerializer)
from .utils import generate_shopping_cart_pdf

User = get_user_model()


class UsersViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """ViewSet for viewing, creating, and modifying User instances."""

    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):  # type: ignore
        """Return context-specific serializer classes based on the action."""
        if self.action == 'create':
            return UsersCreateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=None)
    def current_user(self, request):
        """Retrieve the profile data of the currently authenticated user."""
        return Response(self.get_serializer(request.user).data,
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=AvatarSerializer)
    def user_image(self, request):
        """Update or completely remove the authenticated user's avatar
        image."""
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
        """Verify the current password and set a new password for the user."""
        if not request.user.check_password(request.data['current_password']):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(request.data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', 'delete'), url_path='subscribe',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=FollowingSerializer)
    def subscribe(self, request, pk=None, *args, **kwargs):
        """Follow or unfollow an author identified by their primary key
        (pk)."""
        get_object_or_404(User, id=pk)
        if request.method == 'POST':
            return self.create(request, *args, **kwargs)
        if request.method == 'DELETE':
            deleted, _ = Following.objects.filter(user=request.user,
                                                  following_id=pk).delete()
            if not deleted:
                raise ValidationError(
                    'Вы не были подписаны на этого пользователя.')
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',), url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=FollowingSerializer,)
    def subscriptions(self, request, *args, **kwargs):
        """Return a paginated list of authors followed by the active user."""
        self.queryset = User.objects.filter(
            author_relations__user=request.user)
        return self.list(request, *args, **kwargs)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for browsing individual ingredients or catalogs."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for browsing configured tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing standard CRUD interactions for Recipe records."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitPageNumberPagination
    permission_classes = [IsAuthorOrReadOnly,]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    ordering_fields = ['created_at',]
    ordering = ['-created_at']

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Generate and present a shortened absolute web link for the recipe.
        """
        if self.get_object():
            return Response(
                {'short-link': request.build_absolute_uri(f'/s/{pk}')},
                status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            serializer_class=ShortRecipeSerializer)
    def favorite(self, request, pk):
        """Add a target recipe to or remove it from the user's favorites
        list."""
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
        """Manage adding, deleting, or viewing items inside the shopping
        cart."""
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
        """Aggregate all ingredients from the user's shopping cart and
        download as PDF.

        Queries all ingredients across recipes inside the shopping cart,
        groups them by name and measurement unit, calculates the sum
        of quantities, and generates a downloadable PDF file.
        """
        # Aggregate ingredient totals for all recipes in the shopping cart
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values('ingredients__name', 'ingredients__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredients__name')
        )

        # Generate the PDF file buffer using the utility function
        pdf_buffer = generate_shopping_cart_pdf(list(ingredients))

        # Return the file response as a downloadable attachment
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename='shopping_cart.pdf',
        )
