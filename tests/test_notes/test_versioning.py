"""Tests for note versioning, unified diffs, and reversion."""

import pytest

from markdown_notes.notes.models import Note
from markdown_notes.notes.versioning import (
    compare_two_versions,
    compute_text_diff,
    create_version_snapshot,
    revert_note_to_version,
)
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_compute_text_diff() -> None:
    """Verify unified diff calculation."""
    old_text = "Line 1\nLine 2\nLine 3"
    new_text = "Line 1\nLine 2 modified\nLine 3\nLine 4"
    diff = compute_text_diff(old_text, new_text)

    assert "-Line 2" in diff
    assert "+Line 2 modified" in diff
    assert "+Line 4" in diff


def test_create_version_snapshot_and_sequential_numbering(user: User) -> None:
    """Verify version snapshots increment version_number and capture diffs."""
    note = Note.objects.create(
        user=user,
        title="Doc",
        content="First version text",
    )
    v1 = create_version_snapshot(note, change_summary="v1")
    assert v1.version_number == 1
    assert v1.diff == ""

    note.content = "Second version modified text"
    note.save()
    v2 = create_version_snapshot(note, change_summary="v2")
    assert v2.version_number == 2
    assert "-First version text" in v2.diff
    assert "+Second version modified text" in v2.diff


def test_revert_note_to_version(user: User) -> None:
    """Verify reverting note content to prior version creates rollback snapshot."""
    note = Note.objects.create(
        user=user,
        title="Initial Title",
        content="Initial Content",
    )
    create_version_snapshot(note, change_summary="Created note")

    note.title = "Second Title"
    note.content = "Second Content with new lines"
    note.save()
    create_version_snapshot(note, change_summary="Updated note")

    # Revert to version 1
    updated_note, v3 = revert_note_to_version(note, target_version_number=1)
    assert updated_note.title == "Initial Title"
    assert updated_note.content == "Initial Content"
    assert v3.version_number == 3
    assert "Reverted back to version 1" in v3.change_summary


def test_compare_two_versions(user: User) -> None:
    """Verify comparing two arbitrary version snapshots."""
    note = Note.objects.create(
        user=user,
        title="Comparison Note",
        content="Alpha",
    )
    v1 = create_version_snapshot(note)

    note.content = "Beta"
    note.save()
    v2 = create_version_snapshot(note)

    diff = compare_two_versions(v1, v2)
    assert "-Alpha" in diff
    assert "+Beta" in diff
