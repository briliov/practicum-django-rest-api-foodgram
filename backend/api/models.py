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


class Ingredient(NamedModel):
    """Model Ingredient"""
    measurement_unit = models.CharField('Ingredient measurement unit',
                                        max_length=256)

    class Meta(NamedModel.Meta):
        """Meta class for model Ingredient"""
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name}'
