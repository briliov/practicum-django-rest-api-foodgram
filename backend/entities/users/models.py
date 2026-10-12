"""Models for users application."""


from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q


class User(AbstractUser):
    """Custom user model."""

    email = models.EmailField(unique=True,
                              verbose_name="Пользовательская почта")
    avatar = models.ImageField(
        upload_to="users/", blank=True,
        verbose_name="Пользовательская аватарка",
    )
    first_name = models.CharField(max_length=150, blank=False,
                                  verbose_name="Имя")
    last_name = models.CharField(max_length=150, blank=False,
                                 verbose_name="Фамилия")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        """Meta class for model User."""

        verbose_name = "Кастомный пользователь"
        verbose_name_plural = "Кастомные пользователи"
        ordering = ("email",)

    def __str__(self):
        """Return string explanation for model."""
        return self.email


class Following(models.Model):
    """Users following model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписывающийся",
        related_name="subscriptions",
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="На кого подписываются",
        related_name="subscribers",
    )

    class Meta:
        """Meta class for model Following."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_user_following",
            ),
            models.CheckConstraint(
                condition=~Q(user=F("following")),
                name="failure_self_following",
            ),
        )
        ordering = ("user",)

    def __str__(self):
        """Return string explanation for model."""
        return f"«{self.user}» подписан на «{self.following}»"
