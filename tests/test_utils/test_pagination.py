"""Tests for pagination utilities and health check endpoint."""

import pytest
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from markdown_notes.notes.models import Note
from markdown_notes.users.models import User
from markdown_notes.utils.pagination import (
    NoteCursorPagination,
    StandardResultsSetPagination,
)

pytestmark = pytest.mark.django_db


def test_standard_pagination(user: User) -> None:
    """Verify StandardResultsSetPagination pages results."""
    for i in range(25):
        Note.objects.create(user=user, title=f"Note {i}", content=f"Body {i}")

    factory = APIRequestFactory()
    wsgi_request = factory.get("/api/notes/?page=1&page_size=10")
    drf_request = Request(wsgi_request)

    paginator = StandardResultsSetPagination()
    qs = Note.objects.filter(user=user).order_by("created_at")
    page = paginator.paginate_queryset(qs, drf_request)
    assert page is not None
    assert len(page) == 10

    response = paginator.get_paginated_response([n.title for n in page])
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 10


def test_cursor_pagination(user: User) -> None:
    """Verify NoteCursorPagination generates cursors."""
    for i in range(5):
        Note.objects.create(user=user, title=f"Note {i}", content=f"Body {i}")

    factory = APIRequestFactory()
    wsgi_request = factory.get("/api/notes/")
    drf_request = Request(wsgi_request)

    paginator = NoteCursorPagination()
    paginator.page_size = 2
    qs = Note.objects.filter(user=user).order_by("-created_at")
    page = paginator.paginate_queryset(qs, drf_request)
    assert page is not None
    assert len(page) == 2


def test_health_check_endpoint(api_client: APIClient) -> None:
    """Verify health check returns healthy status and DB vendor."""
    response = api_client.get("/api/health/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "healthy"
    assert response.data["database"] == "connected"
    assert "vendor" in response.data
