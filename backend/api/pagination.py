from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE_QUERY_PARAM, RECIPES_LIMIT


class CustomPagination(PageNumberPagination):
    page_size = RECIPES_LIMIT
    page_size_query_param = PAGE_SIZE_QUERY_PARAM
