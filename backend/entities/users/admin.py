"""Admin panel configuration for users application models."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe
from rest_framework.authtoken.models import TokenProxy as Token

from entities.recipes.admin import RecipeCountMixin

from .models import Following, User

admin.site.site_header = "Панель управления Foodgram"
admin.site.site_title = "Админ панель Foodgram"
admin.site.index_title = "Добро пожаловать в управление проектом!"

admin.site.unregister((Group, Token))


@admin.register(User)
class CustomUserAdmin(RecipeCountMixin, UserAdmin):
    """Admin panel interface configurations for managing CustomUser models."""

    list_display = (
        "id",
        "username",
        "get_full_name",
        "email",
        "get_image",
        "get_subscribers_count",
    ) + RecipeCountMixin.list_display
    search_fields = ("username", "email")
    fieldsets = UserAdmin.fieldsets + (  # type: ignore
        ("Дополнительно", {"fields": ("avatar", "get_subscribers_count")}),
    )
    readonly_fields = (
        "get_subscribers_count",
    ) + RecipeCountMixin.list_display

    def get_queryset(self, request):
        """Get User queryset with annotated subscribers_count count."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            subscribers_count=Count("subscribers", distinct=True),
        )

    @admin.display(description="Аватарка")
    def get_image(self, obj):
        """Return HTML preview of the user profile avatar."""
        if obj.avatar:
            html_content = f"""
                <div style="display: flex; gap: 10px; align-items: center;">
                    <img src="{obj.avatar.url}" style="width: 50px; height:
                    50px; object-fit: cover; border-radius: 4px;">
                </div>
            """
            return mark_safe(html_content)
        return "Нет аватара"

    @admin.display(description="ФИО")
    def get_full_name(self, obj):
        """Return string explanation user full name."""
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="Количество подписчиков")
    def get_subscribers_count(self, obj):
        """Discplays subscribers count."""
        return obj.subscribers_count


@admin.register(Following)
class FollowingAdmin(admin.ModelAdmin):
    """Admin panel interface configurations for managing Following models."""

    list_display = ("user", "following")
    list_filter = ("user__username", "user", "following")
    search_fields = (
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "following__email",
        "following__username",
        "following__first_name",
        "following__last_name",
    )
