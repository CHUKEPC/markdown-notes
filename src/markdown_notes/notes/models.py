"""Database models for notes, categories, tags, and version history."""

import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Category model for grouping user notes into high-level subjects."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="Owner of the category.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name of the category.",
    )
    slug = models.SlugField(
        max_length=120,
        help_text="URL-friendly identifier unique per user.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Optional description of the category.",
    )
    color = models.CharField(
        max_length=20,
        default="#3b82f6",
        help_text="Hex color code for UI presentation (e.g. #3b82f6).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when category was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when category was last updated.",
    )

    class Meta:
        db_table = "note_categories"
        verbose_name_plural = "categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_category_name_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "slug"],
                name="unique_category_slug_per_user",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-populate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """String representation of category."""
        return self.name


class Tag(models.Model):
    """Tag model for cross-cutting labels attached to notes."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
        help_text="Owner of the tag.",
    )
    name = models.CharField(
        max_length=50,
        help_text="Tag label.",
    )
    slug = models.SlugField(
        max_length=60,
        help_text="URL-friendly identifier unique per user.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when tag was created.",
    )

    class Meta:
        db_table = "note_tags"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_tag_name_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "slug"],
                name="unique_tag_slug_per_user",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-populate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """String representation of tag."""
        return self.name


class Note(models.Model):
    """Note model holding Markdown content and rendered HTML."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the note.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
        help_text="Owner of the note.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the note.",
    )
    content = models.TextField(
        help_text="Raw Markdown content.",
    )
    rendered_html = models.TextField(
        blank=True,
        default="",
        help_text="Server-rendered sanitized HTML output.",
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notes",
        help_text="Optional category group.",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="notes",
        help_text="Tags associated with this note.",
    )
    is_pinned = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this note is pinned to top of lists.",
    )
    is_favorite = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this note is marked as favorite.",
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this note is archived.",
    )
    share_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="Secret URL token allowing public view access.",
    )
    is_shared = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether public sharing is currently active.",
    )
    share_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration timestamp for the public share link.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when note was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Timestamp when note was last updated.",
    )

    class Meta:
        db_table = "notes"
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self) -> str:
        """String representation of note."""
        return self.title


class NoteVersion(models.Model):
    """Historical snapshot of a note created on update operations."""

    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="Reference to the parent note.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Sequential version number starting at 1.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Note title at this revision.",
    )
    content = models.TextField(
        help_text="Raw Markdown content at this revision.",
    )
    change_summary = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Brief summary or commit message for this edit.",
    )
    diff = models.TextField(
        blank=True,
        default="",
        help_text="Unified diff against previous version content.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when version snapshot was captured.",
    )

    class Meta:
        db_table = "note_versions"
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["note", "version_number"],
                name="unique_version_per_note",
            ),
        ]

    def __str__(self) -> str:
        """String representation of note version."""
        return f"{self.note.title} v{self.version_number}"
