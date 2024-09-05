from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import RecipePermission
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeListSerializer,
                          RecipeShortLinkSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, SubscriptionsSerializer,
                          TagSerializer, UserAvatarSerializer)
from .utils import add_recipe, delete_recipe
from food.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                         Recipe, ShoppingCart, Tag)

User = get_user_model()


def redirect_to_original(request, short_code):
    recipe = get_object_or_404(Recipe, short_url=short_code)
    host = request.get_host()
    url = urljoin(f'{host}', f'{recipe.id}')
    return redirect(reverse(url))


@api_view(['PUT', 'DELETE'])
def user_avatar(request):
    """Добавляет, меняет или удаляет аватар пользователю"""
    user = User.objects.get(email=request.user.email)
    if request.method == 'PUT':
        if request.user.avatar:
            request.user.avatar.delete()
        serializer = UserAvatarSerializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user.avatar.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
def favorite(request, recipe_id):
    """
    Удаление/добавление рецептов в избранное.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'DELETE':
        error_message = f'Рецепт {recipe} не добавлен в избранное'
        return delete_recipe(
            request, Favorite, recipe, error_message
        )
    return add_recipe(request, recipe, FavoriteSerializer)


@api_view(['POST', 'DELETE'])
def shopping_cart(request, recipe_id):
    """
    Удаление/добавление рецепта в список покупок.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    if request.method == 'DELETE':
        error_message = f'Рецепт {recipe} не добавлен в список покупок'
        return delete_recipe(
            request, ShoppingCart, recipe, error_message
        )
    return add_recipe(request, recipe, ShoppingCartSerializer)


@api_view(['GET'])
def download_shopping_cart(request):
    """Отправка файла со списком покупок."""
    ingredients = IngredientRecipe.objects.filter(
        recipe__shoppingcart__user=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(ingredient_amount=Sum('amount'))
    shopping_list = ['Список покупок:\n']
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['ingredient_amount']
        shopping_list.append(f'\n{name} - {amount}, {unit}')
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"')
    return response


class RecipeLinkView(APIView):
    """Вьюсет для коротких ссылок."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
            if not recipe.short_url:
                recipe.short_url = recipe.generate_short_url()
                recipe.save(update_fields=['short_url'])
            serializer = RecipeShortLinkSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Recipe not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (RecipePermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FollowListViewSet(ListAPIView, viewsets.GenericViewSet):
    """Вьюсет для подписок."""
    serializer_class = SubscriptionsSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class RecipeShortLinkViewSet(ListAPIView, viewsets.GenericViewSet):
    """Вьюсет для коротких линков."""
    serializer_class = RecipeShortLinkSerializer

    def get_queryset(self):
        return Recipe.objects.filter(id=self.request.recipe_id)


class FollowView(APIView):
    """Создание/удаление подписки на пользователя."""
    def post(self, request, user_id):
        following = get_object_or_404(User, id=user_id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        following = get_object_or_404(User, id=user_id)
        if not Follow.objects.filter(user=request.user,
                                     following=following).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(user=request.user.id,
                           following=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
