"""Application configuration module for the infrastructure backend API."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    """Configuration class for the api application package."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = _('Интерфейс API')
