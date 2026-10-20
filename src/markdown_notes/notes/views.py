"""REST API ViewSets and Views for managing notes, tags, categories, and sharing."""

import json
from typing import Any

from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from markdown_notes.notes.filters import NoteFilter
from markdown_notes.notes.models import Category, Note, NoteVersion, Tag
from markdown_notes.notes.permissions import IsOwner
from markdown_notes.notes.serializers import (
    CategorySerializer,
    NoteCreateUpdateSerializer,
    NoteDetailSerializer,
    NoteListSerializer,
    NoteVersionSerializer,
    PublicSharedNoteSerializer,
    ShareCreateSerializer,
    TagSerializer,
)
from markdown_notes.notes.services import NoteService
from markdown_notes.notes.versioning import compare_two_versions, revert_note_to_version
from markdown_notes.users.models import User


class CategoryViewSet(viewsets.ModelViewSet[Category]):
    """CRUD ViewSet for managing note categories."""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self) -> Any:
        """Return categories belonging exclusively to the authenticated user."""
        assert isinstance(self.request.user, User)
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer: BaseSerializer[Category]) -> None:
        """Associate category with the authenticated user upon creation."""
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet[Tag]):
    """CRUD ViewSet for managing note tags."""

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self) -> Any:
        """Return tags belonging exclusively to the authenticated user."""
        assert isinstance(self.request.user, User)
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer: BaseSerializer[Tag]) -> None:
        """Associate tag with the authenticated user upon creation."""
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet[Note]):
    """ViewSet providing full CRUD, versioning, sharing, and import/export for notes."""

    permission_classes = [IsAuthenticated, IsOwner]
    filterset_class = NoteFilter
    ordering_fields = ["created_at", "updated_at", "title", "is_pinned", "is_favorite"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self) -> Any:
        """Return notes belonging exclusively to current user with prefetched relations."""
        assert isinstance(self.request.user, User)
        return (
            Note.objects.filter(user=self.request.user)
            .select_related("category")
            .prefetch_related("tags")
        )

    def get_serializer_class(self) -> Any:
        """Return appropriate serializer depending on the request action."""
        if self.action == "list":
            return NoteListSerializer
        if self.action in ("create", "update", "partial_update"):
            return NoteCreateUpdateSerializer
        return NoteDetailSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new note using NoteService."""
        serializer = NoteCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        category = None
        if data.get("category_id"):
            category = get_object_or_404(
                Category,
                id=data["category_id"],
                user=request.user,
            )

        note = NoteService.create_note(
            user=request.user,  # type: ignore[arg-type]
            title=data["title"],
            content=data["content"],
            category=category,
            tag_names=data.get("tags", []),
            is_pinned=data.get("is_pinned", False),
            is_favorite=data.get("is_favorite", False),
        )

        output_serializer = NoteDetailSerializer(note)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update existing note using NoteService and track revision history."""
        note = self.get_object()
        serializer = NoteCreateUpdateSerializer(
            data=request.data, partial=kwargs.get("partial", False)
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        category = None
        category_set = "category_id" in data
        if category_set and data.get("category_id") is not None:
            category = get_object_or_404(
                Category,
                id=data["category_id"],
                user=request.user,
            )

        note = NoteService.update_note(
            note=note,
            title=data.get("title"),
            content=data.get("content"),
            category=category,
            category_set=category_set,
            tag_names=data.get("tags") if "tags" in data else None,
            change_summary=data.get("change_summary", ""),
            is_pinned=data.get("is_pinned"),
            is_favorite=data.get("is_favorite"),
            is_archived=data.get("is_archived"),
        )

        output_serializer = NoteDetailSerializer(note)
        return Response(output_serializer.data)

    @action(detail=True, methods=["post"], url_path="pin")
    def pin(self, request: Request, pk: str | None = None) -> Response:
        """Toggle pinned status of note."""
        note = self.get_object()
        is_pinned = NoteService.toggle_pin(note)
        return Response(
            {
                "id": str(note.id),
                "is_pinned": is_pinned,
                "message": f"Note {'pinned' if is_pinned else 'unpinned'} successfully.",
            }
        )

    @action(detail=True, methods=["post"], url_path="favorite")
    def favorite(self, request: Request, pk: str | None = None) -> Response:
        """Toggle favorite status of note."""
        note = self.get_object()
        is_favorite = NoteService.toggle_favorite(note)
        return Response(
            {
                "id": str(note.id),
                "is_favorite": is_favorite,
                "message": f"Note {'added to' if is_favorite else 'removed from'} favorites.",
            }
        )

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request: Request, pk: str | None = None) -> Response:
        """Generate or refresh a public share link for the note."""
        note = self.get_object()
        serializer = ShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expires_in_days = serializer.validated_data.get("expires_in_days")
        note = NoteService.create_share_link(note, expires_in_days=expires_in_days)

        share_url = request.build_absolute_uri(f"/api/notes/shared/{note.share_token}/")
        return Response(
            {
                "share_token": note.share_token,
                "share_url": share_url,
                "expires_at": note.share_expires_at,
                "message": "Share link generated successfully.",
            }
        )

    @action(detail=True, methods=["post"], url_path="revoke-share")
    def revoke_share(self, request: Request, pk: str | None = None) -> Response:
        """Revoke and deactivate public share access."""
        note = self.get_object()
        NoteService.revoke_share_link(note)
        return Response({"message": "Public share link revoked successfully."})

    @action(detail=True, methods=["get"], url_path="versions")
    def list_versions(self, request: Request, pk: str | None = None) -> Response:
        """List historical revision snapshots for the note."""
        note = self.get_object()
        versions = note.versions.all().order_by("-version_number")
        serializer = NoteVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path=r"versions/(?P<version_num>[0-9]+)")
    def get_version(
        self, request: Request, pk: str | None = None, version_num: str = "1"
    ) -> Response:
        """Retrieve a specific version snapshot."""
        note = self.get_object()
        version = get_object_or_404(NoteVersion, note=note, version_number=int(version_num))
        serializer = NoteVersionSerializer(version)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path=r"versions/(?P<version_num>[0-9]+)/revert")
    def revert_version(
        self, request: Request, pk: str | None = None, version_num: str = "1"
    ) -> Response:
        """Revert note content to a previous version."""
        note = self.get_object()
        target_version_num = int(version_num)
        reverted_note, new_version = revert_note_to_version(note, target_version_num)

        return Response(
            {
                "message": f"Successfully reverted to version {target_version_num}.",
                "current_version": new_version.version_number,
                "note": NoteDetailSerializer(reverted_note).data,
            }
        )

    @action(detail=True, methods=["get"], url_path=r"versions/(?P<version_num>[0-9]+)/diff")
    def diff_version(
        self, request: Request, pk: str | None = None, version_num: str = "1"
    ) -> Response:
        """Compare a version against another version (compare_to param)."""
        note = self.get_object()
        v1 = get_object_or_404(NoteVersion, note=note, version_number=int(version_num))

        compare_to_str = request.query_params.get("compare_to")
        if compare_to_str and compare_to_str.isdigit():
            v2 = get_object_or_404(NoteVersion, note=note, version_number=int(compare_to_str))
        else:
            latest_v = note.versions.order_by("-version_number").first()
            if latest_v is None:
                return Response({"diff": ""})
            v2 = latest_v

        diff_text = compare_two_versions(v1, v2)
        return Response(
            {
                "from_version": v1.version_number,
                "to_version": v2.version_number,
                "diff": diff_text,
            }
        )

    @action(detail=True, methods=["get"], url_path="export")
    def export_single(self, request: Request, pk: str | None = None) -> HttpResponse:
        """Export single note in Markdown or JSON format."""
        note = self.get_object()
        export_format = (
            request.query_params.get("export_format")
            or request.query_params.get("type")
            or "markdown"
        ).lower()

        if export_format in ("json",):
            data = NoteService.export_note_json(note)
            return HttpResponse(
                json.dumps(data, indent=2),
                content_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{slugify(note.title)}.json"'
                },
            )

        # Default markdown export
        md_text = NoteService.export_note_markdown(note)
        return HttpResponse(
            md_text,
            content_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{slugify(note.title)}.md"'},
        )

    @action(detail=False, methods=["get"], url_path="export-all")
    def export_all(self, request: Request) -> HttpResponse:
        """Export all user notes as a downloadable ZIP archive containing markdown files."""
        zip_bytes = NoteService.export_all_notes_zip(request.user)  # type: ignore[arg-type]
        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="notes_export.zip"'
        return response

    @action(detail=False, methods=["post"], url_path="import")
    def import_notes(self, request: Request) -> Response:
        """Import notes from uploaded .md file or JSON payload."""
        uploaded_file = request.FILES.get("file")
        if uploaded_file:
            filename = uploaded_file.name
            try:
                content = uploaded_file.read().decode("utf-8")
            except UnicodeDecodeError:
                return Response(
                    {"error": "Uploaded file must be UTF-8 encoded text."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            note = NoteService.import_note_from_markdown(
                user=request.user,  # type: ignore[arg-type]
                filename=filename,
                file_text=content,
            )
            return Response(
                {
                    "message": "Note imported successfully.",
                    "notes": [NoteDetailSerializer(note).data],
                },
                status=status.HTTP_201_CREATED,
            )

        # Check for JSON notes array
        notes_data = request.data.get("notes") if isinstance(request.data, dict) else None
        if isinstance(notes_data, list):
            created = NoteService.import_notes_from_json(request.user, notes_data)  # type: ignore[arg-type]
            return Response(
                {
                    "message": f"Successfully imported {len(created)} notes.",
                    "notes": NoteListSerializer(created, many=True).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "error": "Please provide a markdown file under 'file' or a JSON array under 'notes'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class SharedNoteView(APIView):
    """Public read-only endpoint for viewing shared notes via token."""

    permission_classes = [AllowAny]

    def get(self, request: Request, share_token: str) -> Response:
        """Return publicly accessible note data or error if expired."""
        note = NoteService.get_shared_note(share_token)
        serializer = PublicSharedNoteSerializer(note)
        return Response(serializer.data)


class HealthCheckView(APIView):
    """Service health check endpoint reporting DB connection status."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Verify database connectivity and return health report."""
        db_healthy = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_healthy = False

        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(
            {
                "status": "healthy" if db_healthy else "unhealthy",
                "database": "connected" if db_healthy else "disconnected",
                "vendor": connection.vendor,
            },
            status=status_code,
        )
