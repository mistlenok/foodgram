from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('tags', views.TagViewSet, basename='tags')
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('users/subscriptions', views.FollowListViewSet,
                basename='subscriptions')

urlpatterns = [
    path('users/me/avatar/', views.user_avatar),
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/download_shopping_cart/', views.download_shopping_cart),
    path('users/<int:user_id>/subscribe/', views.FollowView.as_view()),
    path('recipes/<int:recipe_id>/favorite/', views.favorite),
    path('recipes/<int:recipe_id>/shopping_cart/', views.shopping_cart),
    path('recipes/<int:recipe_id>/get-link/', views.RecipeLinkView.as_view(),
         name='short_link'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
