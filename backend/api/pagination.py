from rest_framework.pagination import PageNumberPagination

from .constants import RECIPE_QUERY_PARAM, RECIPES_LIMIT


class RecipePagination(PageNumberPagination):
    page_size = RECIPES_LIMIT
    page_size_query_param = RECIPE_QUERY_PARAM
