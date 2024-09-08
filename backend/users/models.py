from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models

from .constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, USERNAME_REGEXP


class User(AbstractUser):
    """Модель пользователя"""
    username = models.CharField(
        'Имя пользователя',
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=[validators.RegexValidator(USERNAME_REGEXP)],
        error_messages={
            'unique': 'A user with that username already exists.',
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
        ordering = ('-id',)

    def __str__(self):
        return self.username


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
                fields=['user', 'following']),
            models.CheckConstraint(
                name='user_and_following_are_different',
                check=~models.Q(user=models.F('following'))
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
