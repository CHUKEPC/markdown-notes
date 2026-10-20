"""Integration tests for Category, Tag, and Note ViewSets."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from markdown_notes.notes.models import Category, Note, Tag
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_category_crud_and_user_isolation(
    auth_client: APIClient,
    other_auth_client: APIClient,
    user: User,
    other_user: User,
) -> None:
    """Verify Category CRUD and strict user isolation."""
    # Create category for user
    res = auth_client.post(
        "/api/categories/",
        {"name": "Frontend", "description": "React & CSS", "color": "#10b981"},
        format="json",
    )
    assert res.status_code == status.HTTP_201_CREATED
    cat_id = res.data["id"]

    # Other user cannot see this category
    other_res = other_auth_client.get("/api/categories/")
    assert other_res.status_code == status.HTTP_200_OK
    assert len(other_res.data["results"]) == 0

    # Other user cannot update or delete this category
    update_res = other_auth_client.put(
        f"/api/categories/{cat_id}/",
        {"name": "Hacked"},
        format="json",
    )
    assert update_res.status_code == status.HTTP_404_NOT_FOUND


def test_tag_crud_and_user_isolation(
    auth_client: APIClient,
    other_auth_client: APIClient,
) -> None:
    """Verify Tag CRUD and strict user isolation."""
    res = auth_client.post("/api/tags/", {"name": "Security"}, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    tag_id = res.data["id"]

    # Other user does not see user's tags
    other_res = other_auth_client.get("/api/tags/")
    assert len(other_res.data["results"]) == 0

    # Delete tag
    del_res = auth_client.delete(f"/api/tags/{tag_id}/")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT


def test_note_crud_lifecycle(auth_client: APIClient, category: Category, tag: Tag) -> None:
    """Verify full CRUD lifecycle for notes."""
    payload = {
        "title": "Backend Architecture",
        "content": "# Clean API\n\nBuilt with Django REST Framework.",
        "category_id": category.id,
        "tags": [tag.name, "API"],
        "is_pinned": True,
        "is_favorite": False,
    }
    create_res = auth_client.post("/api/notes/", payload, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    note_id = create_res.data["id"]
    assert create_res.data["title"] == "Backend Architecture"
    assert "<h1>Clean API</h1>" in create_res.data["rendered_html"]
    assert create_res.data["versions_count"] == 1

    # Retrieve detail
    get_res = auth_client.get(f"/api/notes/{note_id}/")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.data["title"] == "Backend Architecture"

    # Update note
    update_res = auth_client.put(
        f"/api/notes/{note_id}/",
        {
            "title": "Backend Architecture v2",
            "content": "# Clean API v2\n\nUpdated with new endpoints.",
            "change_summary": "Added new routes",
        },
        format="json",
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.data["title"] == "Backend Architecture v2"
    assert update_res.data["versions_count"] == 2

    # Delete note
    del_res = auth_client.delete(f"/api/notes/{note_id}/")
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
    assert not Note.objects.filter(id=note_id).exists()


def test_note_user_isolation(
    auth_client: APIClient,
    other_auth_client: APIClient,
    note: Note,
) -> None:
    """Verify users cannot view, edit, or delete each other's notes."""
    # other_auth_client cannot view note
    res = other_auth_client.get(f"/api/notes/{note.id}/")
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # other_auth_client cannot modify note
    put_res = other_auth_client.put(f"/api/notes/{note.id}/", {"title": "Exploit", "content": "x"})
    assert put_res.status_code == status.HTTP_404_NOT_FOUND


def test_note_filtering_and_sorting(auth_client: APIClient, user: User) -> None:
    """Verify filtering notes by tag, category, pinned, favorite, and search."""
    cat1 = Category.objects.create(user=user, name="Category A", slug="cat-a")
    cat2 = Category.objects.create(user=user, name="Category B", slug="cat-b")

    t1 = Tag.objects.create(user=user, name="SpecialTag")

    n1 = Note.objects.create(
        user=user,
        title="Note 1 Machine Learning",
        content="TensorFlow and PyTorch models",
        category=cat1,
        is_pinned=True,
    )
    n1.tags.add(t1)

    Note.objects.create(
        user=user,
        title="Note 2 Web Development",
        content="React and CSS Grid",
        category=cat2,
        is_favorite=True,
    )

    # Filter by category slug
    res = auth_client.get("/api/notes/?category=cat-a")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.data["results"]) == 1
    assert res.data["results"][0]["id"] == str(n1.id)

    # Filter by tag
    res_tag = auth_client.get("/api/notes/?tag=SpecialTag")
    assert len(res_tag.data["results"]) == 1

    # Filter by search
    res_search = auth_client.get("/api/notes/?search=TensorFlow")
    assert len(res_search.data["results"]) == 1

    # Filter by pinned
    res_pinned = auth_client.get("/api/notes/?is_pinned=true")
    assert len(res_pinned.data["results"]) == 1


def test_note_actions_pin_and_favorite(auth_client: APIClient, note: Note) -> None:
    """Verify pin and favorite action endpoints."""
    # Unpin note (was created pinned)
    pin_res = auth_client.post(f"/api/notes/{note.id}/pin/")
    assert pin_res.status_code == status.HTTP_200_OK
    assert pin_res.data["is_pinned"] is False

    # Favorite toggle
    fav_res = auth_client.post(f"/api/notes/{note.id}/favorite/")
    assert fav_res.status_code == status.HTTP_200_OK
    assert fav_res.data["is_favorite"] is False


def test_note_versions_endpoints(auth_client: APIClient, note: Note) -> None:
    """Verify version history listing, version detail, diff, and reversion endpoints."""
    # Update note to generate version 2
    auth_client.put(
        f"/api/notes/{note.id}/",
        {"title": note.title, "content": "Modified content for v2"},
        format="json",
    )

    # List versions
    list_res = auth_client.get(f"/api/notes/{note.id}/versions/")
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.data) == 2

    # Get version 1
    v1_res = auth_client.get(f"/api/notes/{note.id}/versions/1/")
    assert v1_res.status_code == status.HTTP_200_OK
    assert v1_res.data["version_number"] == 1

    # Diff version 1 and version 2
    diff_res = auth_client.get(f"/api/notes/{note.id}/versions/1/diff/?compare_to=2")
    assert diff_res.status_code == status.HTTP_200_OK
    assert "+Modified content for v2" in diff_res.data["diff"]

    # Revert to version 1
    revert_res = auth_client.post(f"/api/notes/{note.id}/versions/1/revert/")
    assert revert_res.status_code == status.HTTP_200_OK
    assert revert_res.data["current_version"] == 3
    assert revert_res.data["note"]["content"] == note.content


def test_note_export_endpoints(auth_client: APIClient, note: Note) -> None:
    """Verify single note markdown and json export and all notes zip export."""
    # Export markdown
    md_res = auth_client.get(f"/api/notes/{note.id}/export/?export_format=markdown")
    assert md_res.status_code == status.HTTP_200_OK
    assert md_res.headers["Content-Type"].startswith("text/markdown")
    assert note.title.encode("utf-8") in md_res.content

    # Export JSON
    json_res = auth_client.get(f"/api/notes/{note.id}/export/?export_format=json")
    assert json_res.status_code == status.HTTP_200_OK
    assert json_res.headers["Content-Type"] == "application/json"
    assert note.title.encode("utf-8") in json_res.content

    # Export All as ZIP
    zip_res = auth_client.get("/api/notes/export-all/")
    assert zip_res.status_code == status.HTTP_200_OK
    assert zip_res.headers["Content-Type"] == "application/zip"


def test_note_import_endpoints(auth_client: APIClient) -> None:
    """Verify importing notes via uploaded .md file and json payload."""
    # File upload import
    file_content = b"# Imported via File\n\nContent body"
    upload = SimpleUploadedFile("my_doc.md", file_content, content_type="text/markdown")
    res_file = auth_client.post("/api/notes/import/", {"file": upload}, format="multipart")
    assert res_file.status_code == status.HTTP_201_CREATED
    assert res_file.data["notes"][0]["title"] == "Imported via File"

    # JSON import
    json_payload = {
        "notes": [
            {"title": "Bulk 1", "content": "Body 1"},
            {"title": "Bulk 2", "content": "Body 2"},
        ]
    }
    res_json = auth_client.post("/api/notes/import/", json_payload, format="json")
    assert res_json.status_code == status.HTTP_201_CREATED
    assert len(res_json.data["notes"]) == 2
