"""Models for recipe applocation."""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from utils.constants import (
    AMOUNT_MAX_VALUE,
    AMOUNT_MIN_VALUE,
    BASE_NAME_MAX_LENGTH,
    COOKING_MAX_VALUE,
    COOKING_MIN_VALUE,
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH_VALUE,
    RECIPE_NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH_VALUE,
    TAG_NAME_MAX_LENGTH,
)

User = get_user_model()


class NamedModel(models.Model):
    """Abstract named model."""

    name = models.CharField(
        max_length=BASE_NAME_MAX_LENGTH,
        verbose_name="Имя",
    )

    class Meta:
        """Metadata for abastract class NamedModel."""

        abstract = True
        ordering = ("name",)

    def __str__(self):
        """Return string explanation for model."""
        return f"{self.name}"


class Ingredient(NamedModel):
    """Model Ingredient."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name="Название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH_VALUE,
        verbose_name="Единицы измерения",
    )

    class Meta(NamedModel.Meta):
        """Meta class for model Ingredient."""

        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_name_measurement_unit",
            ),
        ]

    def __str__(self):
        """Return string explanation for model."""
        return f"{self.name} ({self.measurement_unit})"


class Tag(NamedModel):
    """Model Tag."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        verbose_name="Имя т",
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH_VALUE,
        unique=True,
        verbose_name="Имя уникального индефикатора",
    )

    class Meta(NamedModel.Meta):
        """Meta class for model Tag."""

        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Recipe(NamedModel):
    """Model Recipe."""

    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name="Название рецепта",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор рецепта",
    )
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Картинка рецепта",
        null=False,
        blank=False,
    )
    text = models.TextField(verbose_name="Текст рецепта")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингедиенты рецепта",
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги рецепта",
        blank=False,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (мин.)",
        validators=(
            MinValueValidator(
                COOKING_MIN_VALUE,
                message=(
                    "Время приготовления не может быть меньше одной минуты"
                ),
            ),
            MaxValueValidator(
                COOKING_MAX_VALUE,
                message=("Время приготовления не можетбыть больше недели"),
            ),
        ),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добаления рецепта",
    )

    class Meta(NamedModel.Meta):
        """Meta class for model Recipe."""

        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"
        ordering = ("-created_at",)


class RecipeIngredient(models.Model):
    """Recipe - Ingredient model."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингердиенты",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                AMOUNT_MIN_VALUE,
                message="Количество должно быть не менее 1",
            ),
            MaxValueValidator(
                AMOUNT_MAX_VALUE,
                message="Слишком большое количество",
            ),
        ],
    )

    class Meta:
        """Meta class for model RecipeIngredient."""

        verbose_name = "Связь рецепта и ингердиента"
        verbose_name_plural = "Связь рецепта и ингердиента"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            ),
        ]
        default_related_name = "recipe_ingredients"
        ordering = ("recipe__name",)

    def __str__(self):
        """Return string explanation for model."""
        return (
            f"{self.recipe}: {self.ingredient} {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class UserRecipe(models.Model):
    """Abstract user recipe model."""

    user = models.ForeignKey(
        User,
        related_name="%(class)s_set",
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="%(class)s_by",
        verbose_name="Рецепт",
        on_delete=models.CASCADE,
    )

    class Meta:
        """Meta class for model abastact UserRecipe."""

        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(class)s_user_recipe",
            ),
        )
        ordering = ("user", "recipe")

    def __str__(self):
        """Return string explanation for model."""
        return f"«{self.recipe}» в {self.__class__.__name__} у «{self.user}»"


class Favorite(UserRecipe):
    """User avorite recipes model."""

    class Meta(UserRecipe.Meta):
        """Meta class for model Favorite."""

        verbose_name = "Избранные"
        verbose_name_plural = "Избранные"


class ShoppingCart(UserRecipe):
    """User ShoppingCart recipes model."""

    class Meta(UserRecipe.Meta):
        """Meta class for model ShoppingCart."""

        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"
