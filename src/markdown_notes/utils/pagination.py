"""Custom pagination classes for DRF endpoints."""

from rest_framework.pagination import CursorPagination, PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard page-number based pagination with configurable size."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NoteCursorPagination(CursorPagination):
    """Cursor-based pagination optimized for large ordered note collections."""

    page_size = 20
    ordering = "-created_at"
    cursor_query_param = "cursor"
