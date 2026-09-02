"""Models for API."""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Following(models.Model):
    """Users following model."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='User',
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Following',
    )

    class Meta:
        """Meta class for model Following"""
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            )
        ]

    def __str__(self):
        return f'{self.user} followed to {self.following}'


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


class Tag(NamedModel):
    """Model Tag"""
    slug = models.SlugField('Uniq slug', max_length=256, unique=True)

    class Meta(NamedModel.Meta):
        """Meta class for model Tag"""
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return f'{self.name}'
