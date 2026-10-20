"""Tests for custom Django permissions."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from markdown_notes.notes.models import Note
from markdown_notes.notes.permissions import IsOwner, IsOwnerOrSharedReadOnly
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_is_owner_permission(user: User, other_user: User, note: Note) -> None:
    """Verify IsOwner allows owner and denies others or anonymous."""
    perm = IsOwner()
    view = APIView()
    factory = APIRequestFactory()

    # Authenticated owner
    req_owner = Request(factory.get("/"))
    req_owner.user = user  # type: ignore[assignment]
    assert perm.has_object_permission(req_owner, view, note) is True

    # Authenticated other user
    req_other = Request(factory.get("/"))
    req_other.user = other_user  # type: ignore[assignment]
    assert perm.has_object_permission(req_other, view, note) is False

    # Anonymous user
    req_anon = Request(factory.get("/"))
    assert perm.has_object_permission(req_anon, view, note) is False


def test_is_owner_or_shared_read_only(user: User, other_user: User, note: Note) -> None:
    """Verify IsOwnerOrSharedReadOnly allows safe methods for active shared notes."""
    perm = IsOwnerOrSharedReadOnly()
    view = APIView()
    factory = APIRequestFactory()

    # Note not shared: other user denied
    req_other_get = Request(factory.get("/"))
    req_other_get.user = other_user  # type: ignore[assignment]
    assert perm.has_object_permission(req_other_get, view, note) is False

    # Note shared and not expired: other user allowed on GET
    note.is_shared = True
    note.share_expires_at = timezone.now() + timedelta(days=2)
    note.save()
    assert perm.has_object_permission(req_other_get, view, note) is True

    # But denied on POST/PUT
    req_other_put = Request(factory.put("/"))
    req_other_put.user = other_user  # type: ignore[assignment]
    assert perm.has_object_permission(req_other_put, view, note) is False
