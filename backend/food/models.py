from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models

from .constants import (INGREDIENT_MAX_LENGTH, MAX_COOKING_TIME,
                        MAX_MEASURMENT_UNIT, MAX_RECIPE_AMOUNT,
                        MIN_COOKING_TIME, MIN_RECIPE_AMOUNT,
                        RECIPE_NAME_MAX_LENGTH, SHORT_URL_MAX_LENGTH,
                        TAG_MAX_LENGTH)

User = get_user_model()


class Tag(models.Model):
    """Модель тэга"""
    name = models.CharField('Название', unique=True, max_length=TAG_MAX_LENGTH)
    slug = models.SlugField(
        'Уникальный слаг',
        unique=True,
        max_length=TAG_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField(
        'Название',
        max_length=INGREDIENT_MAX_LENGTH,
        unique=True,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_MEASURMENT_UNIT
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""
    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH)
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientRecipe',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True,
        verbose_name='Тэги',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[validators.MinValueValidator(
            MIN_COOKING_TIME,
            message=f'Минимальное значение поля - {MIN_COOKING_TIME}.'),
            validators.MaxValueValidator(
                MAX_COOKING_TIME,
                message=f'Максимальное значение поля - {MAX_COOKING_TIME}.')
        ]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    image = models.ImageField(
        'Фото рецепта',
        upload_to='recipes/images/',
        validators=(
            validators.FileExtensionValidator(
                allowed_extensions=('png', 'jpg', 'jpeg')
            ),
        ),
    )
    short_url = models.CharField(
        max_length=SHORT_URL_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткий URL'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """
    Ингридиенты для рецепта.
    Промежуточная модель между таблицами
    Recipe и Ingredient
    """
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[validators.MinValueValidator(
            MIN_RECIPE_AMOUNT,
            message=f'Минимальное значение поля - {MIN_RECIPE_AMOUNT}.'),
            validators.MaxValueValidator(
                MAX_RECIPE_AMOUNT,
                message=f'Максимальное значение поля - {MAX_RECIPE_AMOUNT}.')
        ]
    )

    class Meta:
        verbose_name = 'Cостав рецепта'
        verbose_name_plural = 'Состав рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients')]

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class BaseFavoriteShopping(models.Model):
    """Вспомогательная модель для избранного и списка покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s_recipe'
            )
        ]

    def __str__(self):
        return (f'{self.user.username} добавил '
                f'{self.recipe.name} в {self._meta.verbose_name}')


class Favorite(BaseFavoriteShopping):
    """Модель избранного"""

    class Meta(BaseFavoriteShopping.Meta):
        ordering = ['-id']
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseFavoriteShopping):
    """Модель списка покупок"""

    class Meta(BaseFavoriteShopping.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Список покупок'
