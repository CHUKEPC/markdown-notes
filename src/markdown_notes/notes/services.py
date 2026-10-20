"""Business logic service layer for notes management."""

import io
import json
import secrets
import zipfile
from datetime import timedelta
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.text import slugify

from markdown_notes.notes.models import Category, Note, Tag
from markdown_notes.notes.renderers import render_markdown_to_html
from markdown_notes.notes.versioning import create_version_snapshot
from markdown_notes.users.models import User


class NoteService:
    """Service encapsulating all operations on notes, tags, sharing, and exports."""

    @staticmethod
    def create_note(
        user: User,
        title: str,
        content: str,
        category: Category | None = None,
        tag_names: list[str] | None = None,
        is_pinned: bool = False,
        is_favorite: bool = False,
    ) -> Note:
        """Create a new note, render HTML, associate tags, and create initial revision.

        Args:
            user: Author of the note.
            title: Title text.
            content: Markdown content.
            category: Optional Category instance.
            tag_names: Optional list of tag names to link.
            is_pinned: Whether note is pinned.
            is_favorite: Whether note is favorite.

        Returns:
            Created Note instance.
        """
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Note title cannot be blank.")

        rendered_html = render_markdown_to_html(content)

        note = Note.objects.create(
            user=user,
            title=clean_title,
            content=content,
            rendered_html=rendered_html,
            category=category,
            is_pinned=is_pinned,
            is_favorite=is_favorite,
        )

        if tag_names:
            tags_to_add: list[Tag] = []
            for tag_name in tag_names:
                tag_name_clean = tag_name.strip()
                if tag_name_clean:
                    tag_slug = slugify(tag_name_clean)
                    tag, _ = Tag.objects.get_or_create(
                        user=user,
                        slug=tag_slug,
                        defaults={"name": tag_name_clean},
                    )
                    tags_to_add.append(tag)
            note.tags.set(tags_to_add)

        # Create initial version 1 snapshot
        create_version_snapshot(note, change_summary="Initial note creation")

        return note

    @staticmethod
    def update_note(
        note: Note,
        title: str | None = None,
        content: str | None = None,
        category: Category | None = None,
        category_set: bool = False,
        tag_names: list[str] | None = None,
        change_summary: str = "",
        is_pinned: bool | None = None,
        is_favorite: bool | None = None,
        is_archived: bool | None = None,
    ) -> Note:
        """Update note attributes and capture version diff if content changed.

        Args:
            note: Existing Note instance.
            title: Optional updated title.
            content: Optional updated content.
            category: Category instance (if category_set is True).
            category_set: Flag specifying if category field was explicitly provided.
            tag_names: Optional list of tag names to associate.
            change_summary: Summary of changes for revision history.
            is_pinned: Optional pinned state update.
            is_favorite: Optional favorite state update.
            is_archived: Optional archived state update.

        Returns:
            Updated Note instance.
        """
        content_or_title_changed = False

        if title is not None:
            clean_title = title.strip()
            if not clean_title:
                raise ValidationError("Note title cannot be blank.")
            if note.title != clean_title:
                note.title = clean_title
                content_or_title_changed = True

        if content is not None and note.content != content:
            note.content = content
            note.rendered_html = render_markdown_to_html(content)
            content_or_title_changed = True

        if category_set:
            note.category = category

        if is_pinned is not None:
            note.is_pinned = is_pinned

        if is_favorite is not None:
            note.is_favorite = is_favorite

        if is_archived is not None:
            note.is_archived = is_archived

        note.save()

        if tag_names is not None:
            tags_to_add: list[Tag] = []
            for tag_name in tag_names:
                clean_tag = tag_name.strip()
                if clean_tag:
                    slug = slugify(clean_tag)
                    tag, _ = Tag.objects.get_or_create(
                        user=note.user,
                        slug=slug,
                        defaults={"name": clean_tag},
                    )
                    tags_to_add.append(tag)
            note.tags.set(tags_to_add)

        # If content or title was altered, save a new version snapshot
        if content_or_title_changed:
            create_version_snapshot(
                note,
                change_summary=change_summary or "Updated note content",
            )

        return note

    @staticmethod
    def toggle_pin(note: Note) -> bool:
        """Toggle pinned state of note and persist change."""
        note.is_pinned = not note.is_pinned
        note.save(update_fields=["is_pinned", "updated_at"])
        return note.is_pinned

    @staticmethod
    def toggle_favorite(note: Note) -> bool:
        """Toggle favorite state of note and persist change."""
        note.is_favorite = not note.is_favorite
        note.save(update_fields=["is_favorite", "updated_at"])
        return note.is_favorite

    @staticmethod
    def create_share_link(note: Note, expires_in_days: int | None = None) -> Note:
        """Generate a public share token with optional expiration."""
        note.share_token = secrets.token_urlsafe(32)
        note.is_shared = True
        if expires_in_days and expires_in_days > 0:
            note.share_expires_at = timezone.now() + timedelta(days=expires_in_days)
        else:
            note.share_expires_at = None
        note.save(update_fields=["share_token", "is_shared", "share_expires_at", "updated_at"])
        return note

    @staticmethod
    def revoke_share_link(note: Note) -> Note:
        """Disable public sharing and clear active share token."""
        note.is_shared = False
        note.share_token = None
        note.share_expires_at = None
        note.save(update_fields=["share_token", "is_shared", "share_expires_at", "updated_at"])
        return note

    @staticmethod
    def get_shared_note(share_token: str) -> Note:
        """Retrieve publicly shared note verifying active and unexpired status."""
        try:
            note = (
                Note.objects.select_related("category", "user")
                .prefetch_related("tags")
                .get(
                    share_token=share_token,
                    is_shared=True,
                )
            )
        except Note.DoesNotExist as err:
            raise PermissionDenied("Shared note does not exist or link is invalid.") from err

        if note.share_expires_at and note.share_expires_at < timezone.now():
            raise PermissionDenied("Share link has expired.")

        return note

    @staticmethod
    def export_note_markdown(note: Note) -> str:
        """Export note to Markdown with YAML frontmatter metadata."""
        tag_list = [tag.name for tag in note.tags.all()]
        category_name = note.category.name if note.category else ""

        frontmatter = [
            "---",
            f"title: {json.dumps(note.title)}",
            f"category: {json.dumps(category_name)}",
            f"tags: {json.dumps(tag_list)}",
            f"created_at: {note.created_at.isoformat()}",
            f"updated_at: {note.updated_at.isoformat()}",
            "---",
            "",
            note.content,
        ]
        return "\n".join(frontmatter)

    @staticmethod
    def export_note_json(note: Note) -> dict[str, Any]:
        """Export single note structure to a JSON-serializable dictionary."""
        return {
            "id": str(note.id),
            "title": note.title,
            "content": note.content,
            "category": note.category.name if note.category else None,
            "tags": [tag.name for tag in note.tags.all()],
            "is_pinned": note.is_pinned,
            "is_favorite": note.is_favorite,
            "is_archived": note.is_archived,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }

    @staticmethod
    def export_all_notes_zip(user: User) -> bytes:
        """Export all user notes as a ZIP file containing Markdown files."""
        notes = Note.objects.filter(user=user).select_related("category").prefetch_related("tags")
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for note in notes:
                file_name = f"{slugify(note.title) or 'untitled'}_{str(note.id)[:8]}.md"
                md_content = NoteService.export_note_markdown(note)
                zip_file.writestr(file_name, md_content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    def import_note_from_markdown(user: User, filename: str, file_text: str) -> Note:
        """Parse uploaded markdown content and create note."""
        lines = file_text.splitlines()
        title = ""
        content_lines: list[str] = []
        tags: list[str] = []
        category_name = ""

        # Parse simple frontmatter if delimited by triple dashes ---
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx]
                if line.startswith("title:"):
                    title = line.split("title:", 1)[1].strip().strip("\"'")
                elif line.startswith("category:"):
                    category_name = line.split("category:", 1)[1].strip().strip("\"'")
                elif line.startswith("tags:"):
                    raw_tags = line.split("tags:", 1)[1].strip()
                    try:
                        parsed_tags = json.loads(raw_tags)
                        if isinstance(parsed_tags, list):
                            tags = [str(t) for t in parsed_tags]
                    except json.JSONDecodeError:
                        tags = [t.strip() for t in raw_tags.strip("[]").split(",") if t.strip()]
                idx += 1
            content_lines = lines[idx + 1 :]
        else:
            content_lines = lines

        body = "\n".join(content_lines).strip()

        # If title wasn't found in frontmatter, try first markdown H1 or filename
        if not title:
            for line in content_lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

        if not title:
            clean_filename = filename.rsplit(".", 1)[0]
            title = clean_filename.replace("-", " ").replace("_", " ").title()

        category = None
        if category_name:
            cat_slug = slugify(category_name)
            category, _ = Category.objects.get_or_create(
                user=user,
                slug=cat_slug,
                defaults={"name": category_name},
            )

        return NoteService.create_note(
            user=user,
            title=title or "Imported Note",
            content=body,
            category=category,
            tag_names=tags,
        )

    @staticmethod
    def import_notes_from_json(user: User, data: list[dict[str, Any]]) -> list[Note]:
        """Bulk import notes from a list of JSON note objects."""
        created_notes: list[Note] = []
        for item in data:
            title = item.get("title", "").strip() or "Untitled Imported Note"
            content = item.get("content", "")
            cat_name = item.get("category")
            tags = item.get("tags", [])
            is_pinned = bool(item.get("is_pinned", False))
            is_favorite = bool(item.get("is_favorite", False))

            category = None
            if cat_name:
                cat_slug = slugify(cat_name)
                category, _ = Category.objects.get_or_create(
                    user=user,
                    slug=cat_slug,
                    defaults={"name": cat_name},
                )

            note = NoteService.create_note(
                user=user,
                title=title,
                content=content,
                category=category,
                tag_names=tags,
                is_pinned=is_pinned,
                is_favorite=is_favorite,
            )
            created_notes.append(note)

        return created_notes
