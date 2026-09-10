"""Application configuration module for the infrastructure backend API."""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Configuration class for the api application package."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
