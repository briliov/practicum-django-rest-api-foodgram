"""Admin panel configuration for recipe application models."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


class RecipeCountMixin:
    """Mixin for counting recipe count.

    Optimize request count and add method display for admin panel.
    """

    list_display = ("get_recipe_add_count",)
    readonly_fields = ("get_recipe_add_count",)

    def get_queryset(self, request):
        """Optimize request count and add method display for admin panel."""
        queryset = super().get_queryset(request)  # type: ignore
        return queryset.annotate(recipe_count=Count("recipes", distinct=True))

    @admin.display(description="Рецепты")
    def get_recipe_add_count(self, obj):
        """Display recipe add count."""
        return obj.recipe_count


class RecipeIngredientInline(admin.TabularInline):
    """Inline formset for adding ingredients on the recipe page."""

    model = RecipeIngredient
    autocomplete_fields = ("ingredient",)
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel interface configurations for managing Recipe models."""

    list_display = (
        "name",
        "author__username",
        "cooking_time",
        "get_tags",
        "get_ingredients",
        "get_image",
        "get_favorite_add_count",
    )
    search_fields = (
        "name",
        "author__username",
        "tags__name",
        "ingredients__name",
    )
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ("tags",)
    list_filter = ("tags", "author__username")

    def get_queryset(self, request):
        """Get Recipe queryset with annotated favorites count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(in_favorites_count=Count("favorite_by"))

    @admin.display(description="Теги")
    def get_tags(self, obj):
        """Display recipe tags html bullet list display."""
        return mark_safe(
            "".join(f"<li>{tag.name}</li>" for tag in obj.tags.all()),
        )

    @admin.display(description="Ингредиенты")
    def get_ingredients(self, obj):
        """Display recipe ingredients html bullet list display."""
        return mark_safe(
            "".join(
                f"<li>{ingredient.name}</li>"
                for ingredient in obj.ingredients.all()
            ),
        )

    @admin.display(description="Картинка")
    def get_image(self, obj):
        """Display recipe image preview."""
        html_content = f"""
            <div style="display: flex; gap: 10px; align-items: center;">
                <img src="{obj.image.url}" style="width: 50px; height:
                50px; object-fit: cover; border-radius: 4px;">
            </div>
            """
        return mark_safe(html_content)

    @admin.display(description="Число добавлений в избранное")
    def get_favorite_add_count(self, obj):
        """Display the total times the recipe was added to favorites."""
        return obj.in_favorites_count


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountMixin, admin.ModelAdmin):
    """Admin panel interface configurations for managing Ingredient models."""

    list_display = (
        "name",
        "measurement_unit",
    ) + RecipeCountMixin.list_display
    search_fields = ("name",)
    list_filter = ("measurement_unit",)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Admin panel configuration for Recipe and Ingredient relations."""

    list_display = ("id", "recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")
    list_filter = ("recipe",)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    """Admin panel interface configurations for managing Tag models."""

    list_display = (
        "name",
        "slug",
    ) + RecipeCountMixin.list_display
    search_fields = ("name",)


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationsAdmin(admin.ModelAdmin):
    """Admin panel interface for Favorite and ShoppingCart models."""

    list_display = (
        "user",
        "recipe",
    )
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user",)
