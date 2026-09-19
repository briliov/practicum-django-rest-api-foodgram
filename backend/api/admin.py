"""Application configuration module for the infrastructure backend API."""

from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (CustomUser, Favorite, Following, Ingredient, Recipe,
                     ShoppingCart, Tag)

admin.site.site_header = 'Панель управления Foodgram'
admin.site.site_title = 'Админ панель Foodgram'
admin.site.index_title = 'Добро пожаловать в управление проетом!'

admin.site.register([Following, Tag, Favorite, ShoppingCart])


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin panel interface configurations for managing CustomUser models."""

    list_display = ('id', 'username', 'email',)
    search_fields = ('username', 'email')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin panel interface configurations for managing Recipe models."""

    list_display = ('name',
                    'author__username',
                    'cooking_time',
                    'get_tags',
                    'get_ingredients',
                    'get_image',
                    'get_favorite_add_count',)
    search_fields = ('name',
                     'author__username',
                     'tags__name',
                     'ingredients__name')
    list_filter = ('tags', 'author__username')

    def get_queryset(self, request):
        """Get Recipe queryset with annotated favorites count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(in_favorites_count=Count('favorites_by'))

    @admin.display(description='Теги')
    def get_tags(self, obj):
        """Displays recipe tags html bullet list display."""
        return mark_safe("".join(f'<li>{tag.name}</li>'
                                 for tag in obj.tags.all()))

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        """Displays recipe ingredients html bullet list display."""
        return mark_safe("".join(f'<li>{ingredient.name}</li>'
                                 for ingredient in obj.ingredients.all()))

    @admin.display(description='Картинка')
    def get_image(self, obj):
        """Displays recipe image preview."""
        html_content = (
            f"""
            <div style="display: flex; gap: 10px; align-items: center;">
                <img src="{obj.image.url}" style="width: 50px; height:
                50px; object-fit: cover; border-radius: 4px;">
            </div>
            """
        )
        return mark_safe(html_content)

    @admin.display(description='Число добавлений в избранное')
    def get_favorite_add_count(self, obj):
        """Display the calculated number of times the previous recipe was added
        to favorites."""
        return obj.in_favorites_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin panel interface configurations for managing Ingredient models."""

    list_display = ('get_capitalized_name', 'measurement_unit')
    search_fields = ('name',)

    @admin.display(description='Имя')
    def get_capitalized_name(self, obj):
        """Formats and retrieves the capitalized name string of the
        ingredient."""

        if obj.name:
            return obj.name.capitalize()
        return ""
