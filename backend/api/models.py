"""Models for API."""
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='avatar'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email


class Following(models.Model):
    """Users following model."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='User',
    )

    following = models.ForeignKey(
        CustomUser,
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


class Recipe(NamedModel):
    """Model Recipe"""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Recipe author',
    )
    image = models.ImageField('Recipe image', upload_to='recipes/images/')
    text = models.TextField('Recipe text')
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Recipe ingredients',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Recipe tags'
    )
    cooking_time = models.PositiveSmallIntegerField('Cooking time')


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredients'),
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='favorites',
        verbose_name='Favorites recipes',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites_by',
        verbose_name='Favorite recipes',
        on_delete=models.CASCADE
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='shopping_cart',
        verbose_name='Favorites recipes',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shopping_carts',
        verbose_name='Favorite recipes',
        on_delete=models.CASCADE
    )
