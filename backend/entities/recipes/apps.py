"""Application configuration module for the users."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecipesConfig(AppConfig):
    """Configuration class for the recipes application package."""

    name = 'entities.recipes'
    verbose_name = _('Рецепты')
