from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from .constants import RECIPES_LIMIT
from .utils import Base64ImageField, add_ingredients
from food.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                         ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if (request and not request.user.is_anonymous):
            return obj.following.filter(user=request.user).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'password', 'id', 'username',
                  'first_name', 'last_name')


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с аватаром пользователя."""
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError(
                {'avatar': 'This field is required.'}
            )
        return super().validate(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={
            'does_not_exist': 'Ингредиент с id {pk_value} не существует.'
        }
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации о рецептах."""
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and obj.favorite.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and obj.shoppingcart.filter(user=request.user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения/удаления рецептов."""
    ingredients = IngredientRecipeWriteSerializer(
        many=True, allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False
    )
    image = Base64ImageField(allow_null=False, allow_empty_file=False)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'This field is required.'}
            )
        return super().validate(data)

    def validate_ingredients(self, value):
        ingredients_set = {ingredient['id'] for ingredient in value}
        if len(ingredients_set) != len(value):
            raise ValidationError(
                {'ingredients': 'Ингридиенты не должны повторяться!'})
        return value

    def validate_tags(self, value):
        tags_set = set(value)
        if len(tags_set) != len(value):
            raise ValidationError(
                {'tags': 'Теги не должны повторяться!'})
        return value

    def validate_image(self, image):
        if self.context.get('request').method == 'POST' and not image:
            raise serializers.ValidationError('Нужно загрузить изображение.')
        return image

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        add_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        add_ingredients(ingredients, instance)
        tags = validated_data.pop('tags')
        instance.tags.set(tags, clear=True)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeSmallSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с краткой информацией о рецепте."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор коротких ссылок"""
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        short_code = obj.short_url
        return request.build_absolute_uri(f'/s/{short_code}/')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('short_link')
        return representation


class SubscriptionsSerializer(CustomUserSerializer):
    """Сериализатор для получения подписок."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count',
                            'avatar')

    def get_recipes(self, obj):
        """Получает список рецептов."""
        request = self.context.get('request')
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes = obj.recipes.all()[:int(recipes_limit)]
                except (ValueError, TypeError):
                    pass
        return RecipeSmallSerializer(
            recipes[:RECIPES_LIMIT], many=True,
            context={'request': request}).data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/удаления подписки на пользователей."""

    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following'],
                message='Подписка на пользователя уже существует'
            )
        ]

    def validate_following(self, value):
        if self.context['request'].user == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return value

    def to_representation(self, instance):
        request = self.context.get('request')
        return SubscriptionsSerializer(
            instance.following, context={'request': request}
        ).data


class BaseFavoriteShoppingCartSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранных рецептов и списка покупок"""
    class Meta:
        abstract = True
        fields = '__all__'

    def validate(self, attrs):
        model = self.Meta.model
        user = attrs['user']
        recipe = attrs['recipe']

        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError({
                'non_field_errors': [
                    f'Рецепт уже добавлен в {model._meta.verbose_name}'
                ]
            })
        return attrs

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeSmallSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class FavoriteSerializer(BaseFavoriteShoppingCartSerializer):
    """Сериализатор для работы с избранными рецептами."""
    class Meta(BaseFavoriteShoppingCartSerializer.Meta):
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(BaseFavoriteShoppingCartSerializer):
    """Сериализатор для работы со списком покупок."""
    class Meta(BaseFavoriteShoppingCartSerializer.Meta):
        model = ShoppingCart
        fields = '__all__'
