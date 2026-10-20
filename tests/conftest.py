"""Pytest configuration, fixtures, and helpers for tests."""

from typing import Any

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from markdown_notes.notes.models import Category, Note, Tag
from markdown_notes.notes.services import NoteService
from markdown_notes.users.models import User


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def user(db: Any) -> User:
    """Return a test user instance."""
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="ValidPassword123!",
        bio="Test user biography",
    )


@pytest.fixture
def other_user(db: Any) -> User:
    """Return a second distinct test user instance."""
    return User.objects.create_user(
        username="otheruser",
        email="otheruser@example.com",
        password="ValidPassword123!",
        bio="Other user biography",
    )


@pytest.fixture
def auth_client(user: User) -> APIClient:
    """Return an authenticated APIClient for test user."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def other_auth_client(other_user: User) -> APIClient:
    """Return an authenticated APIClient for other_user."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=other_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def category(user: User) -> Category:
    """Return a sample Category owned by test user."""
    return Category.objects.create(
        user=user,
        name="Tech",
        slug="tech",
        description="Technical and engineering notes",
        color="#2563eb",
    )


@pytest.fixture
def tag(user: User) -> Tag:
    """Return a sample Tag owned by test user."""
    return Tag.objects.create(
        user=user,
        name="Python",
        slug="python",
    )


@pytest.fixture
def note(user: User, category: Category, tag: Tag) -> Note:
    """Return a sample Note owned by test user."""
    note = NoteService.create_note(
        user=user,
        title="Python Cheatsheet",
        content="# Python Cheatsheet\n\nHere are some **useful** tips:\n- List comprehensions\n- Decorators",
        category=category,
        tag_names=[tag.name, "Django"],
        is_pinned=True,
        is_favorite=True,
    )
    return note
