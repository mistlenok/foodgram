from django.contrib import admin
from django.db.models import Count

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


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


# @admin.register(Tag.recipes.through)
# class TagRecipe(admin.ModelAdmin):
#     list_display = ('id', 'recipe__name', 'Tag__slug')


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


admin.site.register(Tag.recipes.through)
