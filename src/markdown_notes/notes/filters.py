"""Filter sets for query filtering on notes."""

import django_filters
from django.db.models import QuerySet

from markdown_notes.notes.models import Note
from markdown_notes.notes.search import search_notes


class NoteFilter(django_filters.FilterSet):  # type: ignore[misc]
    """FilterSet providing query parameter filters for note collections."""

    tag = django_filters.CharFilter(
        method="filter_by_tag", help_text="Filter by tag name or slug."
    )
    category = django_filters.CharFilter(
        method="filter_by_category",
        help_text="Filter by category slug or ID.",
    )
    is_pinned = django_filters.BooleanFilter(
        field_name="is_pinned",
        help_text="Filter pinned notes.",
    )
    is_favorite = django_filters.BooleanFilter(
        field_name="is_favorite",
        help_text="Filter favorite notes.",
    )
    is_archived = django_filters.BooleanFilter(
        field_name="is_archived",
        help_text="Filter archived notes.",
    )
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        help_text="Filter notes created at or after timestamp.",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        help_text="Filter notes created at or before timestamp.",
    )
    updated_after = django_filters.DateTimeFilter(
        field_name="updated_at",
        lookup_expr="gte",
        help_text="Filter notes updated at or after timestamp.",
    )
    updated_before = django_filters.DateTimeFilter(
        field_name="updated_at",
        lookup_expr="lte",
        help_text="Filter notes updated at or before timestamp.",
    )
    search = django_filters.CharFilter(
        method="filter_by_search",
        help_text="Full-text search query across title, content, tags.",
    )

    class Meta:
        model = Note
        fields = [
            "is_pinned",
            "is_favorite",
            "is_archived",
        ]

    def filter_by_tag(self, queryset: QuerySet[Note], name: str, value: str) -> QuerySet[Note]:
        """Filter notes matching a tag by slug or name."""
        if not value:
            return queryset
        return queryset.filter(tags__slug__iexact=value) | queryset.filter(
            tags__name__iexact=value
        )

    def filter_by_category(
        self, queryset: QuerySet[Note], name: str, value: str
    ) -> QuerySet[Note]:
        """Filter notes matching a category by ID or slug."""
        if not value:
            return queryset
        if value.isdigit():
            return queryset.filter(category_id=int(value))
        return queryset.filter(category__slug=value)

    def filter_by_search(self, queryset: QuerySet[Note], name: str, value: str) -> QuerySet[Note]:
        """Execute full-text search with relevance ranking."""
        return search_notes(queryset, value)
