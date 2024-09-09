import base64
import hashlib

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response

from .constants import MAX_HASH
from food.models import IngredientRecipe, Recipe


class Base64ImageField(serializers.ImageField):
    """Класс для обработки изображений"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='img.' + ext)
        return super().to_internal_value(data)


def add_ingredients(ingredients, recipe):
    """Вспомогательная функция для создания/редактирования рецептов"""
    IngredientRecipe.objects.order_by('ingredient__name').bulk_create(
        [
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ],
        ignore_conflicts=True
    )


def add_recipe(request, pk, serializer_name):
    """
    Вспомогательная функция для добавления
    рецепта в избранное либо список покупок.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    serializer = serializer_name(
        data={'user': request.user.id, 'recipe': recipe.id},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_recipe(request, pk, model_name):
    """
    Вспомогательная функция для удаления рецепта
    из избранного либо из списка покупок.
    """
    recipe = get_object_or_404(Recipe, id=pk)
    obj = model_name.objects.filter(user=request.user, recipe=recipe)
    if obj.exists():
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'errors': f'Рецепт с id {pk} не добавлен в список покупок'},
        status=status.HTTP_400_BAD_REQUEST)


def generate_short_url(recipe_id):
    """Вспомогательная функция для генерации коротких ссылок"""
    hash_object = hashlib.md5(str(recipe_id).encode())
    return hash_object.hexdigest()[:MAX_HASH]
