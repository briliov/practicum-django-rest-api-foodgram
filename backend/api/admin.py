"""Application configuration module for the infrastructure backend API."""

from django.contrib import admin

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

    list_display = ('name', 'get_author_name')
    search_fields = ('name', 'author__username')
    list_filter = ['tags',]
    readonly_fields = ['get_favorite_add_count',]

    @admin.display(description='Автор')
    def get_author_name(self, obj):
        """Retrieves the username of the recipe author or a default string."""
        if obj.author:
            return obj.author.username
        return "Без автора"

    @admin.display(description='Число добавлений в избранное')
    def get_favorite_add_count(self, obj):
        """Calculates the aggregate count of users who favorited the recipe."""
        return Favorite.objects.filter(recipe=obj).count()


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
            return obj.name.upper() + obj.name[1:1]
        return ""
