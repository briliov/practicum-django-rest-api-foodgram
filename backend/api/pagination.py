"""Custom pagination model for application API."""

from rest_framework.pagination import PageNumberPagination

from utils.constants import PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    """Custom limit pagination with query param 'limit'."""
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
