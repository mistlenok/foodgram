from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.utils.translation import gettext as _

from .constants import (EMAIL_MAX_LENGTH, INGREDIENT_MAX_LENGTH,
                        MAX_MEASURMENT_UNIT, MIN_COOKING_TIME,
                        MIN_RECIPE_AMOUNT, NAME_MAX_LENGTH,
                        RECIPE_NAME_MAX_LENGTH, SHORT_URL_MAX_LENGTH,
                        TAG_MAX_LENGTH, USERNAME_REGEXP)
from .utils import generate_hash


class User(AbstractUser):
    """Модель пользователя"""
    username = models.CharField(
        _('username'),
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=[validators.RegexValidator(USERNAME_REGEXP)],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        db_index=True,
        max_length=EMAIL_MAX_LENGTH
    )
    first_name = models.CharField('Имя', max_length=NAME_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to='users/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'password']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return self.username


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
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[validators.MinValueValidator(
            MIN_COOKING_TIME,
            message=f'Минимальное значение поля - {MIN_COOKING_TIME}.'
        )
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
        upload_to='recipes/',
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
        verbose_name='Короткий URL'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = self.generate_short_url()
        super().save(*args, **kwargs)

    def generate_short_url(self):
        """Функция для генерации коротких ссылок"""
        short_url = generate_hash()
        while Recipe.objects.filter(short_url=short_url).exists():
            short_url = generate_hash()
        return short_url

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
    amount = models.IntegerField(
        'Количество',
        validators=[validators.MinValueValidator(
            MIN_RECIPE_AMOUNT,
            message=f'Минимальное значение поля - {MIN_RECIPE_AMOUNT}.'
        )
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


class Favorite(BaseFavoriteShopping):
    """Модель избранного"""

    class Meta(BaseFavoriteShopping.Meta):
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe'
            )
        ]
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избранное'


class ShoppingCart(BaseFavoriteShopping):
    """Модель списка покупок"""

    class Meta(BaseFavoriteShopping.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart_recipe'
            )
        ]
        verbose_name = 'список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (f'{self.user.username} добавил'
                f'{self.recipe.name} в список покупок'
                )


class Follow(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follows')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_together',
                fields=['user', 'following'])
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return (f'{self.user.username} подписался'
                f' на {self.following.username}'
                )
