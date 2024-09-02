from rest_framework.pagination import PageNumberPagination

from .constants import RECIPES_LIMIT


class CustomPagination(PageNumberPagination):
    page_size = RECIPES_LIMIT
