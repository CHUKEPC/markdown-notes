"""DRF Serializers for notes, categories, tags, and versions."""

from typing import Any

from rest_framework import serializers

from markdown_notes.notes.models import Category, Note, NoteVersion, Tag


class CategorySerializer(serializers.ModelSerializer[Category]):
    """Serializer for Note categories."""

    notes_count = serializers.IntegerField(source="notes.count", read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "color",
            "notes_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "notes_count", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer[Tag]):
    """Serializer for Note tags."""

    notes_count = serializers.IntegerField(source="notes.count", read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
            "notes_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "notes_count", "created_at"]


class NoteVersionSerializer(serializers.ModelSerializer[NoteVersion]):
    """Serializer for note revision history snapshots."""

    class Meta:
        model = NoteVersion
        fields = [
            "id",
            "version_number",
            "title",
            "content",
            "change_summary",
            "diff",
            "created_at",
        ]
        read_only_fields = fields


class NoteListSerializer(serializers.ModelSerializer[Note]):
    """Compact serializer for note listing views."""

    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    snippet = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "snippet",
            "category",
            "tags",
            "is_pinned",
            "is_favorite",
            "is_archived",
            "is_shared",
            "created_at",
            "updated_at",
        ]

    def get_snippet(self, obj: Note) -> str:
        """Return truncated text snippet for fast list previews."""
        first_line = obj.content.strip().split("\n")[0] if obj.content else ""
        return first_line[:150]


class NoteDetailSerializer(serializers.ModelSerializer[Note]):
    """Full detail serializer with rendered HTML and sharing info."""

    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    versions_count = serializers.IntegerField(source="versions.count", read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "content",
            "rendered_html",
            "category",
            "tags",
            "is_pinned",
            "is_favorite",
            "is_archived",
            "is_shared",
            "share_token",
            "share_expires_at",
            "versions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "rendered_html",
            "is_shared",
            "share_token",
            "share_expires_at",
            "versions_count",
            "created_at",
            "updated_at",
        ]


class NoteCreateUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for creating or updating notes."""

    title = serializers.CharField(max_length=255, required=True)
    content = serializers.CharField(required=True, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
    )
    change_summary = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )
    is_pinned = serializers.BooleanField(required=False, default=False)
    is_favorite = serializers.BooleanField(required=False, default=False)
    is_archived = serializers.BooleanField(required=False, default=False)


class ShareCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for configuring a public note share link."""

    expires_in_days = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=365,
        help_text="Optional expiration in days (1 to 365). Omit or null for non-expiring.",
    )


class PublicSharedNoteSerializer(serializers.ModelSerializer[Note]):
    """Serializer exposed on unauthenticated public shared note endpoints."""

    category = serializers.CharField(source="category.name", read_only=True, default=None)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")  # type: ignore[var-annotated]
    author_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Note
        fields = [
            "title",
            "rendered_html",
            "content",
            "category",
            "tags",
            "author_username",
            "updated_at",
            "share_expires_at",
        ]
