from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Follow, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag, User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_staff')
    empty_value_display = 'Не заполнено'
    list_editable = ('is_staff',)
    search_fields = ('username', 'email')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    empty_value_display = 'Не заполнено'
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    empty_value_display = 'Не заполнено'
    search_fields = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time', 'favorited_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author')
    raw_id_fields = ('author',)
    filter_horizontal = ('tags',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            favorited_count=Count('favorite'))

    @admin.display(description='Сколько раз добавлен в избранное')
    def favorited_count(self, request):
        return request.favorited_count


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user')
    search_fields = ('recipe__name', 'user__username')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user')
    search_fields = ('recipe__name', 'user__username')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
