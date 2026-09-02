"""Models for API."""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class NamedModel(models.Model):
    """Abstract named model."""
    name = models.CharField('Name', max_length=256)

    class Meta:
        abstract = True

    def __str__(self):
        """String explanation for model"""
        return f'{self.name}'
