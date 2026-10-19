"""Views for API users and recipe application.

This module provides ViewSets for handling User profiles, Follow relationships,
Ingredients, Tags, and Recipe interactions (including Favorites and Shopping
Cart).
"""

from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Prefetch,
    Sum,
    Value,
    Window,
)
from django.db.models.functions import RowNumber
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from entities.recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from entities.users.models import Following

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientsSerializer,
    ReadRecipeSerializer,
    RecipeUserSubscribeSerializer,
    ShortRecipeSerializer,
    TagSerializer,
    UserSubscribeSerializer,
    WriteRecipeSerializer,
)
from .utils import generate_shopping_cart_pdf

User = get_user_model()


class UsersViewSet(UserViewSet):
    """ViewSet for viewing, creating, and modifying User instances."""

    serializer_class = UserSubscribeSerializer
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        """Obtain a sample with annotated and limited data."""
        queryset = super().get_queryset()

        is_subscribed = Value(False, output_field=BooleanField())
        if self.request.user.is_authenticated:
            is_subscribed = Exists(
                Following.objects.filter(
                    user=self.request.user,
                    following=OuterRef("id"),
                ),
            )
        queryset = queryset.annotate(is_subscribed=is_subscribed)

        if self.action == "subscriptions":
            queryset = queryset.filter(subscribers__user=self.request.user)

        if self.action in ("subscribe", "subscriptions"):
            queryset = queryset.annotate(recipes_count=Count("recipes"))
            recipes_limit = self.request.query_params.get("recipes_limit")
            if recipes_limit and recipes_limit.isdigit():
                queryset = queryset.prefetch_related("recipes")
                limit = int(recipes_limit)
                subquery = (
                    Recipe.objects.filter(
                        author_id=OuterRef(
                            "author_id",
                        ),
                    )
                    .annotate(
                        row_num=Window(
                            expression=RowNumber(),
                            order_by="-id",
                        ),
                    )
                    .values("pk")
                )
                recipes_queryset = Recipe.objects.filter(
                    pk__in=subquery[:limit],
                )

                queryset = queryset.prefetch_related(
                    Prefetch(
                        "recipes",
                        queryset=recipes_queryset,
                        to_attr="limited_recipes",
                    ),
                )

        return queryset

    def get_instance(self):
        """Return a user through a request."""
        return self.get_queryset().get(pk=self.request.user.pk)

    def get_permissions(self):
        """Returns a list of permissions depending on the current action"""
        if self.action in ("me", "post", "update"):
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=("put",),
        url_path="me/avatar",
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=AvatarSerializer,
    )
    def change_user_image(self, request):
        """Update or remove the authenticated user's avatar image."""
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @change_user_image.mapping.delete  # type: ignore
    def delete_user_image(self, request):
        """Remove the authenticated user's avatar."""
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post",),
        url_path="subscribe",
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=RecipeUserSubscribeSerializer,
    )
    def subscribe(self, request, id=None):
        """Follow an author identified by their primary key (pk)."""
        following = get_object_or_404(self.get_queryset(), id=id)
        if request.user == following:
            raise ValidationError(
                {"errors": "Вы не можете подписаться на самого себя."},
            )
        if Following.objects.filter(
            user=self.request.user,
            following=following,
        ).exists():
            raise ValidationError(
                {"error": "Вы не можете подписаться дважды."},
            )
        Following.objects.create(user=self.request.user, following=following)
        updated_following = get_object_or_404(self.get_queryset(), id=id)
        return Response(
            self.get_serializer(updated_following).data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete  # type: ignore
    def unsubscribe(self, request, id=None, *args, **kwargs):
        """Unfollow an author identified by their primary key (pk)."""
        if not User.objects.filter(id=id).exists():
            raise NotFound("Пользователь не найден.")
        deleted, _ = Following.objects.filter(
            user=request.user,
            following_id=id,
        ).delete()
        if not deleted:
            raise ValidationError("Вы не были подписаны на этого пользователя")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("get",),
        url_path="subscriptions",
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=RecipeUserSubscribeSerializer,
    )
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
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    serializer_class = ReadRecipeSerializer

    def get_serializer_class(self):  # type: ignore
        """Return the serializer class based on the current action."""
        if self.action in ("create", "update", "partial_update"):
            return WriteRecipeSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """Save the object with the current user as the author."""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Receiving an annotated sample."""
        queryset = super().get_queryset()
        is_favorited = Value(False, output_field=BooleanField())
        is_in_shopping_cart = Value(False, output_field=BooleanField())
        if self.request.user.is_authenticated:
            is_favorited = Exists(
                Favorite.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef("pk"),
                ),
            )
            is_in_shopping_cart = Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef("pk"),
                ),
            )
        queryset = queryset.annotate(is_favorited=is_favorited).annotate(
            is_in_shopping_cart=is_in_shopping_cart,
        )
        author_queryset = User.objects.all()
        is_subscribed = Value(False, output_field=BooleanField())
        if self.request.user.is_authenticated:
            is_subscribed = Exists(
                Following.objects.filter(
                    user=self.request.user,
                    following=OuterRef("id"),
                ),
            )
        author_queryset = author_queryset.annotate(is_subscribed=is_subscribed)
        queryset = queryset.prefetch_related(
            Prefetch("author", queryset=author_queryset),
        )
        return queryset

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """Generate a shortened absolute web link for the recipe."""
        if not self.get_queryset().filter(pk=pk).exists():
            raise NotFound("Рецепт не найден.")
        return Response(
            {"short-link": request.build_absolute_uri(f"/s/{pk}")},
            status=status.HTTP_200_OK,
        )

    def _add_to_relation(self, request, model):
        """Link the recipe to the current user."""
        recipe = self.get_object()
        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            raise ValidationError("Этот рецепт уже добавлен.")
        serializer = ShortRecipeSerializer(
            recipe,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_relation(self, request, model):
        """Unlink the recipe from the current user."""
        deleted_count, _ = model.objects.filter(
            user=request.user,
            recipe=self.get_object(),
        ).delete()
        if not deleted_count:
            raise ValidationError("Рецепт не был добавлен.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Add the recipe to favorites."""
        return self._add_to_relation(request, Favorite)

    @favorite.mapping.delete  # type: ignore
    def delete_favorite(self, request, pk=None):
        """Remove the recipe from favorites."""
        return self._remove_from_relation(request, Favorite)

    @action(
        detail=True,
        methods=["post"],
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Add the recipe to the shopping cart."""
        return self._add_to_relation(request, ShoppingCart)

    @shopping_cart.mapping.delete  # type: ignore
    def delete_shopping_cart(self, request, pk=None):
        """Remove the recipe from the shopping cart."""
        return self._remove_from_relation(request, ShoppingCart)

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=(IsAuthenticated,),
    )
    def download_shoping_cart(self, request):
        """Aggregate shopping cart ingredients and download as PDF."""
        ingredients = [
            {
                "name": recipe_ingredient["ingredient__name"],
                "unit": recipe_ingredient["ingredient__measurement_unit"],
                "amount": recipe_ingredient["total_amount"],
            }
            for recipe_ingredient in RecipeIngredient.objects.filter(
                recipe__shoppingcart_by__user=request.user,
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        ]

        pdf_buffer = generate_shopping_cart_pdf(ingredients)

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename="shopping_cart.pdf",
        )


def redirect_short_link(request, pk):
    """Redirect page with a short link to the recipe frontend."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f"/recipes/{recipe.pk}")
