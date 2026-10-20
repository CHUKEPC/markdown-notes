"""Tests for NoteService business logic layer."""

import io
import zipfile
from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from markdown_notes.notes.models import Category
from markdown_notes.notes.services import NoteService
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_create_note_service(user: User) -> None:
    """Verify note creation renders HTML, associates tags, and sets version 1."""
    note = NoteService.create_note(
        user=user,
        title="Quick Notes",
        content="# Hello\n\n- item",
        tag_names=["Quick", "Demo"],
    )
    assert note.title == "Quick Notes"
    assert "<h1>Hello</h1>" in note.rendered_html
    assert note.tags.count() == 2
    assert note.versions.count() == 1
    assert note.versions.first().version_number == 1


def test_create_note_blank_title_validation(user: User) -> None:
    """Verify validation error when title is empty string."""
    with pytest.raises(ValidationError):
        NoteService.create_note(user=user, title="   ", content="content")


def test_update_note_service(user: User) -> None:
    """Verify updating note records new version when content changes."""
    note = NoteService.create_note(user=user, title="Original", content="Old body")
    assert note.versions.count() == 1

    updated = NoteService.update_note(
        note=note,
        title="Modified Title",
        content="New body text",
        change_summary="Refined body",
    )
    assert updated.title == "Modified Title"
    assert updated.content == "New body text"
    assert updated.versions.count() == 2
    latest_v = updated.versions.first()
    assert latest_v.version_number == 2
    assert "-Old body" in latest_v.diff
    assert "+New body text" in latest_v.diff


def test_toggle_pin_and_favorite(user: User) -> None:
    """Verify toggling pinned and favorite states."""
    note = NoteService.create_note(user=user, title="Pin Test", content="...")
    assert not note.is_pinned
    assert not note.is_favorite

    assert NoteService.toggle_pin(note) is True
    assert note.is_pinned is True

    assert NoteService.toggle_favorite(note) is True
    assert note.is_favorite is True


def test_sharing_and_expiration(user: User) -> None:
    """Verify public share token generation, expiration check, and revocation."""
    note = NoteService.create_note(user=user, title="Shared Spec", content="Specs...")
    NoteService.create_share_link(note, expires_in_days=7)

    assert note.is_shared is True
    assert note.share_token is not None
    assert note.share_expires_at is not None

    # Retrieve valid shared note
    retrieved = NoteService.get_shared_note(note.share_token)
    assert retrieved == note

    # Test expired link raises PermissionDenied
    note.share_expires_at = timezone.now() - timedelta(days=1)
    note.save()
    with pytest.raises(PermissionDenied):
        NoteService.get_shared_note(note.share_token)

    # Test revoke
    NoteService.revoke_share_link(note)
    assert note.is_shared is False
    assert note.share_token is None


def test_export_and_import_markdown(user: User) -> None:
    """Verify exporting and importing note via markdown."""
    cat = Category.objects.create(user=user, name="Architecture")
    note = NoteService.create_note(
        user=user,
        title="System Design",
        content="Detailed system breakdown.",
        category=cat,
        tag_names=["HighLevel"],
    )

    md_output = NoteService.export_note_markdown(note)
    assert "---" in md_output
    assert 'title: "System Design"' in md_output

    # Import markdown into another note
    imported = NoteService.import_note_from_markdown(
        user=user,
        filename="system_design.md",
        file_text=md_output,
    )
    assert imported.title == "System Design"
    assert imported.content == "Detailed system breakdown."
    assert imported.category.name == "Architecture"


def test_export_all_notes_zip(user: User) -> None:
    """Verify exporting all notes into zip archive."""
    NoteService.create_note(user=user, title="Doc 1", content="Body 1")
    NoteService.create_note(user=user, title="Doc 2", content="Body 2")

    zip_bytes = NoteService.export_all_notes_zip(user)
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        names = z.namelist()
        assert len(names) == 2


def test_import_notes_from_json(user: User) -> None:
    """Verify bulk importing notes from JSON array."""
    data = [
        {"title": "Note A", "content": "Alpha", "tags": ["tag1"], "category": "Cat A"},
        {"title": "Note B", "content": "Beta", "is_pinned": True},
    ]
    created = NoteService.import_notes_from_json(user, data)
    assert len(created) == 2
    assert created[0].title == "Note A"
    assert created[1].is_pinned is True
