"""Tests for user authentication, registration, logout, and profile views."""

import pytest
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_register_success(api_client: APIClient) -> None:
    """Verify successful user registration returns token and user data."""
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "first_name": "New",
        "last_name": "User",
        "bio": "Hello world",
    }
    response = api_client.post("/api/users/register/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "token" in response.data
    assert response.data["user"]["username"] == "newuser"
    assert response.data["user"]["email"] == "newuser@example.com"
    assert User.objects.filter(username="newuser").exists()


def test_register_password_mismatch(api_client: APIClient) -> None:
    """Verify validation error when passwords do not match."""
    payload = {
        "username": "mismatch",
        "email": "mismatch@example.com",
        "password": "PasswordOne1!",
        "password_confirm": "PasswordTwo2!",
    }
    response = api_client.post("/api/users/register/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_confirm" in response.data


def test_login_success(api_client: APIClient, user: User) -> None:
    """Verify successful authentication returns valid token."""
    payload = {
        "username": "testuser",
        "password": "ValidPassword123!",
    }
    response = api_client.post("/api/users/login/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.data
    token = Token.objects.get(key=response.data["token"])
    assert token.user == user


def test_login_invalid_credentials(api_client: APIClient, user: User) -> None:
    """Verify error response on invalid login credentials."""
    payload = {
        "username": "testuser",
        "password": "WrongPassword!",
    }
    response = api_client.post("/api/users/login/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_logout_success(auth_client: APIClient, user: User) -> None:
    """Verify logging out deletes the active authentication token."""
    assert Token.objects.filter(user=user).exists()
    response = auth_client.post("/api/users/logout/")
    assert response.status_code == status.HTTP_200_OK
    assert not Token.objects.filter(user=user).exists()


def test_logout_unauthorized(api_client: APIClient) -> None:
    """Verify unauthenticated logout request is rejected."""
    response = api_client.post("/api/users/logout/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_profile(auth_client: APIClient, user: User) -> None:
    """Verify retrieving current user profile."""
    response = auth_client.get("/api/users/me/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == user.username
    assert response.data["email"] == user.email


def test_update_profile(auth_client: APIClient, user: User) -> None:
    """Verify updating current user profile."""
    payload = {
        "first_name": "UpdatedName",
        "bio": "Updated bio statement",
    }
    response = auth_client.patch("/api/users/me/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "UpdatedName"
    assert response.data["bio"] == "Updated bio statement"

    user.refresh_from_db()
    assert user.first_name == "UpdatedName"
    assert user.bio == "Updated bio statement"
