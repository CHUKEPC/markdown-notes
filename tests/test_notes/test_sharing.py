"""Tests for public note sharing endpoints and token expiration."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from markdown_notes.notes.models import Note

pytestmark = pytest.mark.django_db


def test_public_sharing_workflow(
    auth_client: APIClient,
    api_client: APIClient,
    note: Note,
) -> None:
    """Verify creating share link, public unauthenticated access, and revocation."""
    # Create public share link with 7 days expiration
    share_res = auth_client.post(
        f"/api/notes/{note.id}/share/",
        {"expires_in_days": 7},
        format="json",
    )
    assert share_res.status_code == status.HTTP_200_OK
    share_token = share_res.data["share_token"]
    assert share_token is not None

    # Access shared note without any authentication
    public_res = api_client.get(f"/api/notes/shared/{share_token}/")
    assert public_res.status_code == status.HTTP_200_OK
    assert public_res.data["title"] == note.title
    assert "<h1>Python Cheatsheet</h1>" in public_res.data["rendered_html"]

    # Revoke share link
    revoke_res = auth_client.post(f"/api/notes/{note.id}/revoke-share/")
    assert revoke_res.status_code == status.HTTP_200_OK

    # Public access now fails
    failed_res = api_client.get(f"/api/notes/shared/{share_token}/")
    assert failed_res.status_code == status.HTTP_403_FORBIDDEN


def test_public_sharing_expired_link(
    auth_client: APIClient,
    api_client: APIClient,
    note: Note,
) -> None:
    """Verify expired share link returns 403 Forbidden."""
    share_res = auth_client.post(
        f"/api/notes/{note.id}/share/",
        {"expires_in_days": 1},
        format="json",
    )
    share_token = share_res.data["share_token"]

    # Manually expire the token in database
    note.refresh_from_db()
    note.share_expires_at = timezone.now() - timedelta(hours=1)
    note.save()

    res = api_client.get(f"/api/notes/shared/{share_token}/")
    assert res.status_code == status.HTTP_403_FORBIDDEN
