"""Note revision history and diff management logic."""

import difflib

from markdown_notes.notes.models import Note, NoteVersion
from markdown_notes.notes.renderers import render_markdown_to_html


def compute_text_diff(
    old_text: str, new_text: str, label_old: str = "old", label_new: str = "new"
) -> str:
    """Compute unified diff between two text strings.

    Args:
        old_text: Original text string.
        new_text: Modified text string.
        label_old: Label identifying original text in diff header.
        label_new: Label identifying modified text in diff header.

    Returns:
        Unified diff as formatted string.
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=label_old,
            tofile=label_new,
            lineterm="",
        )
    )
    return "".join(diff_lines)


def create_version_snapshot(note: Note, change_summary: str = "") -> NoteVersion:
    """Create a new version snapshot for the current state of a note.

    Args:
        note: Note model instance to snapshot.
        change_summary: Optional commit message describing the modification.

    Returns:
        Newly created NoteVersion instance.
    """
    latest_version = NoteVersion.objects.filter(note=note).order_by("-version_number").first()

    if latest_version is None:
        version_number = 1
        diff_text = ""
    else:
        version_number = latest_version.version_number + 1
        diff_text = compute_text_diff(
            old_text=latest_version.content,
            new_text=note.content,
            label_old=f"v{latest_version.version_number}",
            label_new=f"v{version_number}",
        )

    version = NoteVersion.objects.create(
        note=note,
        version_number=version_number,
        title=note.title,
        content=note.content,
        change_summary=change_summary or f"Version {version_number}",
        diff=diff_text,
    )
    return version


def revert_note_to_version(note: Note, target_version_number: int) -> tuple[Note, NoteVersion]:
    """Revert a note to a prior version, creating a new reversion snapshot.

    Args:
        note: Note to revert.
        target_version_number: Target version number to restore.

    Returns:
        Tuple of (updated Note, new NoteVersion snapshot).

    Raises:
        NoteVersion.DoesNotExist: If requested version number is not found.
    """
    target_version = NoteVersion.objects.get(
        note=note,
        version_number=target_version_number,
    )

    # Restore fields and re-render safe HTML
    note.title = target_version.title
    note.content = target_version.content
    note.rendered_html = render_markdown_to_html(note.content)
    note.save()

    # Create a new version recording this rollback
    reversion_summary = f"Reverted back to version {target_version_number}"
    new_version = create_version_snapshot(note, change_summary=reversion_summary)

    return note, new_version


def compare_two_versions(v1: NoteVersion, v2: NoteVersion) -> str:
    """Compare content of any two note versions and return unified diff.

    Args:
        v1: Base NoteVersion.
        v2: Target NoteVersion.

    Returns:
        Unified diff string comparing v1 content to v2 content.
    """
    return compute_text_diff(
        old_text=v1.content,
        new_text=v2.content,
        label_old=f"v{v1.version_number}",
        label_new=f"v{v2.version_number}",
    )
