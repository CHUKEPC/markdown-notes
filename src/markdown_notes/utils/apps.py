"""Application configuration for utils module."""

from django.apps import AppConfig


class UtilsConfig(AppConfig):
    """Configuration for utils application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "markdown_notes.utils"
    label = "utils"
