"""Database models for authentication and user accounts."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with unique email and profile attributes."""

    email = models.EmailField(
        unique=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
        help_text="Required. Must be a valid and unique email address.",
    )
    bio = models.TextField(
        blank=True,
        default="",
        help_text="Short user biography or description.",
    )
    avatar_url = models.URLField(
        blank=True,
        default="",
        help_text="Optional URL to user avatar picture.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the user account was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the user account was last updated.",
    )

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """String representation of the user."""
        return self.username
