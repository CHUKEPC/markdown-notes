"""Application configuration for notes module."""

from django.apps import AppConfig


class NotesConfig(AppConfig):
    """Configuration for notes application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "markdown_notes.notes"
    label = "notes"
