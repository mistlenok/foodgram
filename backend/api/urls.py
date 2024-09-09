from django.urls import include, path
from rest_framework import routers

from . import views

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1.register(
    'ingredients', views.IngredientViewSet, basename='ingredients'
)
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')
router_v1.register('users', views.CustomUserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls))
]
