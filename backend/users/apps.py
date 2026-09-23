"""Application configuration module for the users."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """Configuration class for the users application package."""

    name = 'users'
    verbose_name = _('Пользователи')
