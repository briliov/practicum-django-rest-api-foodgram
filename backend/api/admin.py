from django.contrib import admin

from .models import (CustomUser, Following, Ingredient, Tag,
                     Recipe, Favorite, ShoppingCart)


admin.site.site_header = 'Панель управления Foodgram'
admin.site.site_title = 'Админ панель Foodgram'
admin.site.index_title = 'Добро пожаловать в управление проетом!'

admin.site.register([Following,
                     Tag,
                     Favorite,
                     ShoppingCart])


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', )
    search_fields = ('username', 'email')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_author_name')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    readonly_fields = ('get_favorite_add_count',)

    @admin.display(description='Автор')
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.username
        return 'Без автора'

    @admin.display(description='Число добавление в избранное')
    def get_favorite_add_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('get_capitalized_name', 'measurement_unit')
    search_fields = ('name',)

    @admin.display(description='Имя')
    def get_capitalized_name(self, obj):
        if obj.name:
            return obj.name[0].upper() + obj.name[1:]
        return ""
