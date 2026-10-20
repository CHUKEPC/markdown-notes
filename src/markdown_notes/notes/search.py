"""Full-text search service with PostgreSQL tsvector/tsquery and fallback."""

from django.db import connection
from django.db.models import Q, QuerySet

from markdown_notes.notes.models import Note


def search_notes(queryset: QuerySet[Note], query_text: str) -> QuerySet[Note]:
    """Execute full-text search across note title and markdown content.

    Uses PostgreSQL tsvector and tsquery with SearchRank when running against
    a PostgreSQL database. Falls back to multi-field case-insensitive search
    on SQLite for standalone and lightweight testing environments.

    Args:
        queryset: Base QuerySet of Note instances (already user-scoped).
        query_text: Search terms submitted by user.

    Returns:
        Filtered and relevance-ordered QuerySet of Note instances.
    """
    clean_query = query_text.strip()
    if not clean_query:
        return queryset

    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import (
            SearchQuery,
            SearchRank,
            SearchVector,
        )

        # Title matches are weighted higher ('A') than body content ('B')
        search_vector = SearchVector("title", weight="A") + SearchVector("content", weight="B")
        search_query = SearchQuery(clean_query, search_type="websearch")

        return (
            queryset.annotate(
                search_vector=search_vector,
                rank=SearchRank(search_vector, search_query),
            )
            .filter(search_vector=search_query)
            .order_by("-rank", "-is_pinned", "-updated_at")
        )

    # SQLite fallback: search across title, content, tags, and category names
    return queryset.filter(
        Q(title__icontains=clean_query)
        | Q(content__icontains=clean_query)
        | Q(category__name__icontains=clean_query)
        | Q(tags__name__icontains=clean_query)
    ).distinct()
