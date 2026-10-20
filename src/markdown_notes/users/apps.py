"""Application configuration for users module."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration for users application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "markdown_notes.users"
    label = "users"
