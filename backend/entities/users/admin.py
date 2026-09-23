"""Admin panel configuration for users application models."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.db.models import Count

from entities.recipes.admin import RecipeCountMixin
from .models import Following

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(RecipeCountMixin, UserAdmin):
    """Admin panel interface configurations for managing CustomUser models."""

    list_display = ('id',
                    'username',
                    'get_full_name',
                    'email',
                    'get_image',
                    'get_subscribers_count') + RecipeCountMixin.list_display
    search_fields = ('username', 'email')
    readonly_fields = ('get_image',) + RecipeCountMixin.list_display

    def get_queryset(self, request):
        """Get Recipe queryset with annotated favorites count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(subscribers_count=Count('author_relations'),
                                 distinct=True)

    @admin.display(description='Аватарка')
    def get_image(self, obj):
        """Displays User profile avatar preview."""
        if obj.avatar:
            html_content = f"""
                <div style="display: flex; gap: 10px; align-items: center;">
                    <img src="{obj.avatar.url}" style="width: 50px; height:
                    50px; object-fit: cover; border-radius: 4px;">
                </div>
            """
            return mark_safe(html_content)
        return 'Нет аватара'

    @admin.display(description='ФИО')
    def get_full_name(self, obj):
        """Displays user full name."""
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Количество подписчиков')
    def get_subscribers_count(self, obj):
        """Discplays subscribers count."""
        return obj.subscribers_count

admin.site.register([Following])