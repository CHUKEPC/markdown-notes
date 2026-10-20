"""Tests for full-text search capability."""

import pytest

from markdown_notes.notes.models import Category, Note
from markdown_notes.notes.search import search_notes
from markdown_notes.notes.services import NoteService
from markdown_notes.users.models import User

pytestmark = pytest.mark.django_db


def test_search_notes_by_title_and_content(user: User) -> None:
    """Verify notes match on title and body search queries."""
    n1 = NoteService.create_note(
        user=user,
        title="Microservices architecture",
        content="Overview of event driven messaging with RabbitMQ",
    )
    n2 = NoteService.create_note(
        user=user,
        title="PostgreSQL Indexing",
        content="Deep dive into B-Tree, GIN, and tsvector indexes",
    )

    qs = Note.objects.filter(user=user)

    # Search for RabbitMQ (in content of n1)
    results1 = search_notes(qs, "RabbitMQ")
    assert list(results1) == [n1]

    # Search for Indexing (in title of n2)
    results2 = search_notes(qs, "Indexing")
    assert list(results2) == [n2]

    # Empty search returns full queryset
    assert set(search_notes(qs, "   ")) == set(qs)

    # No match
    assert list(search_notes(qs, "KubernetesNonExistent")) == []


def test_search_notes_by_category_and_tags(user: User) -> None:
    """Verify search finds notes linked to matching category or tag labels."""
    cat = Category.objects.create(user=user, name="DevOps")
    note = NoteService.create_note(
        user=user,
        title="CI Pipeline",
        content="GitHub Actions configuration",
        category=cat,
        tag_names=["Automation", "Terraform"],
    )

    qs = Note.objects.filter(user=user)
    assert note in search_notes(qs, "DevOps")
    assert note in search_notes(qs, "Terraform")
