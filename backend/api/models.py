"""Models for API."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model."""
    email = models.EmailField(unique=True,
                              verbose_name='Пользовательская почта')
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='Пользовательская аватарка'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Кастамный пользователь'
        verbose_name_plural = 'Кастамные пользователи'

    def __str__(self):
        """String explanation for model"""
        return self.email


class Following(models.Model):
    """Users following model."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower_relations',
        verbose_name='Подписывающийся'
    )

    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='author_relations',
        verbose_name='На кого подписываются'
    )

    class Meta:
        """Meta class for model Following"""
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            )
        ]

    def __str__(self):
        """String explanation for model"""
        return f'«{self.user}» подписан на «{self.following}»'


class NamedModel(models.Model):
    """Abstract named model."""
    name = models.CharField(max_length=256, verbose_name='Имя')

    class Meta:
        abstract = True
        verbose_name = 'Именнованая модель'
        verbose_name_plural = 'Именнованные модели'

    def __str__(self):
        """String explanation for model"""
        return f'{self.name}'


class Ingredient(NamedModel):
    """Model Ingredient"""
    measurement_unit = models.CharField(max_length=256,
                                        verbose_name='Единицы измерения')

    class Meta(NamedModel.Meta):
        """Meta class for model Ingredient"""
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_measurement_unit'
            )
        ]

    def __str__(self):
        """String explanation for model"""
        return f'{self.name}'


class Tag(NamedModel):
    """Model Tag"""
    slug = models.SlugField(max_length=256, unique=True,
                            verbose_name='Имя уникального индефикатора')

    class Meta(NamedModel.Meta):
        """Meta class for model Tag"""
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """String explanation for model"""
        return f'{self.name}'


class Recipe(NamedModel):
    """Model Recipe"""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    image = models.ImageField(upload_to='recipes/images/',
                              verbose_name='Картинка рецепта')
    text = models.TextField(verbose_name='Текст рецепта')
    ingredients = models.ManyToManyField(Ingredient,
                                         related_name='recipes',
                                         verbose_name='Ингедиенты рецепта')
    tags = models.ManyToManyField(Tag,
                                  related_name='recipes',
                                  verbose_name='Теги рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления')

    class Meta(NamedModel.Meta):
        """Meta class for model Tag"""
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """String explanation for model"""
        return self.name


class RecipeIngredient(models.Model):
    """Recipe - Ingredient model."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                    verbose_name='Ингердиенты')
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta():
        """Meta class for model Tag"""
        verbose_name = 'Связь рецепта и ингердиента'
        verbose_name_plural = 'Связь рецепта и ингердиента'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredients'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """String explanation for model"""
        return (f'{self.recipe}: {self.ingredients} {self.amount} '
                f'{self.ingredients.measurement_unit}')


class Favorite(models.Model):
    """User avorite recipes model."""
    user = models.ForeignKey(CustomUser,
                             related_name='favorites',
                             verbose_name='Пользователь',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               related_name='favorites_by',
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE)

    class Meta():
        """Meta class for model Tag"""
        verbose_name = 'Избранные'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        """String explanation for model"""
        return f'«{self.recipe}» в избранных «{self.user}»'


class ShoppingCart(models.Model):
    """User ShoppingCart recipes model."""
    user = models.ForeignKey(CustomUser,
                             related_name='shopping_cart',
                             verbose_name='Корзина',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               related_name='shopping_carts',
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE)

    class Meta():
        """Meta class for model Tag"""
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        """String explanation for model"""
        return f'«{self.recipe}» в корзине «{self.user}»'
