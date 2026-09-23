"""Models for users application."""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model."""
    email = models.EmailField(unique=True,
                              verbose_name='Пользовательская почта')
    avatar = models.ImageField(upload_to='users/',
                               blank=True,
                               verbose_name='Пользовательская аватарка')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Кастомный пользователь'
        verbose_name_plural = 'Кастомные пользователи'
        ordering = ('email',)

    def __str__(self):
        """String explanation for model"""
        return self.email
