import base64

from django.core.files.base import ContentFile
from rest_framework import serializers, status
from rest_framework.response import Response

from food.models import IngredientRecipe


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
    for ingredient in ingredients:
        current_ingredient = ingredient.get('id')
        amount = ingredient.get('amount')
        IngredientRecipe.objects.update_or_create(
            recipe=recipe,
            ingredient=current_ingredient,
            amount=amount
        )


def add_recipe(request, instance, serializer_name):
    """
    Вспомогательная функция для добавления
    рецепта в избранное либо список покупок.
    """
    serializer = serializer_name(
        data={'user': request.user.id, 'recipe': instance.id},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_recipe(request, model_name, instance, error_message):
    """
    Вспомогательная функция для удаления рецепта
    из избранного либо из списка покупок.
    """
    if not model_name.objects.filter(user=request.user,
                                     recipe=instance).exists():
        return Response({'errors': error_message},
                        status=status.HTTP_400_BAD_REQUEST)
    model_name.objects.filter(user=request.user, recipe=instance).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
