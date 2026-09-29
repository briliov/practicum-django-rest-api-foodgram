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
from django.db.models import Count
from django.db.models import Exists, OuterRef, Value, BooleanField
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .filters import IngredientFilter, RecipeFilter
from entities.recipes.models import (Favorite, Ingredient, Recipe,
                                     RecipeIngredient, ShoppingCart, Tag)
from entities.users.models import Following
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer,
                          IngredientsSerializer, RecipeSerializer,
                          TagSerializer, UserSubscribeSerializer,
                          RecipeUserSubscribeSerializer)
from .utils import generate_shopping_cart_pdf

User = get_user_model()


class UsersViewSet(UserViewSet):
    """ViewSet for viewing, creating, and modifying User instances."""
    serializer_class = UserSubscribeSerializer
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Exists(Following.objects.filter(
                    user=self.request.user, following=OuterRef('id'))))
        else:
            queryset = queryset.annotate(
                is_subscribed=Value(False, output_field=BooleanField()))
        if self.action in ('subscribe', 'subscriptions'):
            queryset = queryset.annotate(recipes_count=Count('recipes')
                                         ).prefetch_related('recipes')
        return queryset

    def get_instance(self):
        return self.get_queryset().get(pk=self.request.user.pk)

    def get_permissions(self):
        if self.action == "me":
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

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
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',), url_path='subscribe',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=RecipeUserSubscribeSerializer)
    def subscribe(self, request, id=None):
        """Follow an author identified by their primary key (pk)."""
        following = get_object_or_404(self.get_queryset(), id=id)
        if request.user == following:
            raise ValidationError(
                {'errors': 'Вы не можете подписаться на самого себя.'})
        if Following.objects.filter(user=self.request.user,
                                    following=following).exists():
            raise ValidationError(
                {'error': 'Вы не можете подписаться дважды.'})
        Following.objects.create(user=self.request.user,
                                 following=following)
        return Response(self.get_serializer(following).data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None, *args, **kwargs):
        """Unfollow an author identified by their primary key (pk)."""
        if not User.objects.filter(id=id).exists():
            raise NotFound('Пользователь не найден.')
        deleted, _ = Following.objects.filter(user=request.user,
                                              following_id=id).delete()
        if not deleted:
            raise ValidationError('Вы не были подписаны на этого пользователя')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',), url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=RecipeUserSubscribeSerializer,)
    def subscriptions(self, request, *args, **kwargs):
        """Return a paginated list of authors followed by the active user."""
        return self.list(request, *args, **kwargs)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for browsing individual ingredients or catalogs."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (AllowAny,)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly ViewSet for browsing configured tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


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
