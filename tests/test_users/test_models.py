"""Tests for custom User model."""

import pytest
from django.db import IntegrityError

from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_user_creation_and_str() -> None:
    """Verify user creation with custom fields and string representation."""
    user = User.objects.create_user(
        username="john_doe",
        email="john@example.com",
        password="SecurePassword456!",
        bio="Software developer",
        avatar_url="https://example.com/avatar.png",
    )
    assert user.username == "john_doe"
    assert user.email == "john@example.com"
    assert user.bio == "Software developer"
    assert user.avatar_url == "https://example.com/avatar.png"
    assert str(user) == "john_doe"
    assert user.check_password("SecurePassword456!")


def test_unique_email_constraint() -> None:
    """Verify that creating two users with the same email raises IntegrityError."""
    User.objects.create_user(
        username="user1",
        email="duplicate@example.com",
        password="Password1!",
    )
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            username="user2",
            email="duplicate@example.com",
            password="Password2!",
        )
