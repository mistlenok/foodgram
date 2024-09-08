from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import RecipePermission
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeListSerializer, RecipeShortLinkSerializer,
                          RecipeWriteSerializer, ShoppingCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserAvatarSerializer)
from .utils import add_recipe, delete_recipe
from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('PUT',),
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='me/avatar'
    )
    def user_avatar(self, request):
        """Добавляет или меняет аватар пользователя."""
        user = self.request.user
        if request.user.avatar:
            request.user.avatar.delete()
        serializer = UserAvatarSerializer(
            user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @user_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('POST',),
        permission_classes=(permissions.IsAuthenticated,),
        detail=True,
        url_path='subscribe'
    )
    def subscribe(self, request, id):
        """Создание подписки на пользователя."""
        following = get_object_or_404(User, pk=id)
        serializer = FollowSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request):
        """Удаление подписки на пользователя."""
        following = get_object_or_404(User, pk=id)
        if not following.following.filter(user=request.user).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(Follow, user=request.user.id,
                          following=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        pagination_class=CustomPagination,
        permission_classes=(permissions.IsAuthenticated,),
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Возвращает все подписки пользователя."""
        queryset = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscriptionsSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionsSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


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

    @action(
        methods=('GET',),
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
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

    @action(
        methods=('POST',),
        permission_classes=(permissions.IsAuthenticated,),
        detail=True,
        url_path='favorite'
    )
    def favorite(self, request, pk):
        """Добавление рецептов в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        return add_recipe(request, recipe, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Удаление рецептов из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        error_message = f'Рецепт {recipe} не добавлен в избранное'
        return delete_recipe(request, Favorite, recipe, error_message)

    @action(
        methods=('POST',),
        permission_classes=(permissions.IsAuthenticated,),
        detail=True,
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        """Добавление рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        return add_recipe(request, recipe, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        """Удаление рецепта из списка покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        error_message = f'Рецепт {recipe} не добавлен в список покупок'
        return delete_recipe(request, ShoppingCart, recipe, error_message)

    @action(
        methods=('GET',),
        detail=True,
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = RecipeShortLinkSerializer(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeShortLinkViewSet(ListAPIView, viewsets.GenericViewSet):
    """Вьюсет для коротких линков."""
    serializer_class = RecipeShortLinkSerializer

    def get_queryset(self):
        return Recipe.objects.filter(id=self.request.recipe_id)


def redirect_to_original(request, short_code):
    """Перенаправление с короткой ссылки на обычную."""
    recipe = get_object_or_404(Recipe, short_url=short_code)
    host = request.get_host()
    url = urljoin(f'http://{host}/api/', f'recipes/{recipe.id}/')
    return redirect(url)
