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
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from entities.recipes.models import (Favorite, Ingredient, Recipe,
                                     RecipeIngredient, ShoppingCart, Tag)
from entities.users.models import Following
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer,
                          IngredientsSerializer, RecipeSerializer,
                          ShortRecipeSerializer, TagSerializer,
                          UserSerializer)
from .utils import generate_shopping_cart_pdf

User = get_user_model()


class UsersViewSet(UserViewSet):
    """ViewSet for viewing, creating, and modifying User instances."""

    @action(detail=False, methods=('put',), url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated],
            serializer_class=AvatarSerializer)
    def change_user_image(self, request):
        """Update or completely remove the authenticated user's avatar
        image."""
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @change_user_image.mapping.delete
    def delete_user_image(self, request):
        """Remove the authenticated user's avatar."""
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',), url_path='subscribe',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer)
    def subscribe(self, request, pk=None, *args, **kwargs):
        """Follow an author identified by their primary key (pk)."""
        return self.create(request, *args, **kwargs)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None, *args, **kwargs):
        """Unfollow an author identified by their primary key (pk)."""
        if not User.objects.filter(id=pk).exists():
            raise NotFound('Пользователь не найден.')
        deleted, _ = Following.objects.filter(user=request.user,
                                              following_id=pk).delete()
        if not deleted:
            raise ValidationError('Вы не были подписаны на этого пользователя')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',), url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer,)
    def subscriptions(self, request, *args, **kwargs):
        """Return a paginated list of authors followed by the active user."""
        self.queryset = self.get_queryset().filter(
            author_relations__user=request.user).prefetch_related('recipes')
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
    permission_classes = [IsAuthorOrReadOnly, ]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    ordering_fields = ['created_at', ]
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
