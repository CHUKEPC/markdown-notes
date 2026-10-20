"""Tests for Category, Tag, Note, and NoteVersion models."""

import pytest
from django.db import IntegrityError

from markdown_notes.notes.models import Category, Note, NoteVersion, Tag
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_category_creation_and_auto_slug(user: User) -> None:
    """Verify category creation auto-generates slug and formats string."""
    cat = Category.objects.create(
        user=user,
        name="Deep Learning",
    )
    assert cat.slug == "deep-learning"
    assert str(cat) == "Deep Learning"


def test_category_unique_constraint(user: User) -> None:
    """Verify unique constraint on (user, name)."""
    Category.objects.create(user=user, name="Work")
    with pytest.raises(IntegrityError):
        Category.objects.create(user=user, name="Work")


def test_tag_creation_and_auto_slug(user: User) -> None:
    """Verify tag creation auto-generates slug and formats string."""
    tag = Tag.objects.create(user=user, name="FastAPI & Django")
    assert tag.slug == "fastapi-django"
    assert str(tag) == "FastAPI & Django"


def test_tag_unique_constraint(user: User) -> None:
    """Verify unique constraint on (user, name)."""
    Tag.objects.create(user=user, name="Architecture")
    with pytest.raises(IntegrityError):
        Tag.objects.create(user=user, name="Architecture")


def test_note_and_version_models(user: User, category: Category, tag: Tag) -> None:
    """Verify note and version creation, relations, and string formatting."""
    note = Note.objects.create(
        user=user,
        title="Architecture Guide",
        content="## Clean Architecture\n\nSeparation of concerns is key.",
        category=category,
    )
    note.tags.add(tag)
    assert str(note) == "Architecture Guide"
    assert note.category == category
    assert note.tags.count() == 1

    version = NoteVersion.objects.create(
        note=note,
        version_number=1,
        title=note.title,
        content=note.content,
        change_summary="Initial commit",
    )
    assert str(version) == "Architecture Guide v1"
    assert note.versions.count() == 1
