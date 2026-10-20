"""URL routes for notes, categories, tags, sharing, and health endpoints."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from markdown_notes.notes.views import (
    CategoryViewSet,
    HealthCheckView,
    NoteViewSet,
    SharedNoteView,
    TagViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"notes", NoteViewSet, basename="note")

urlpatterns = [
    path("notes/shared/<str:share_token>/", SharedNoteView.as_view(), name="note-shared"),
    path("health/", HealthCheckView.as_view(), name="api-health"),
    path("", include(router.urls)),
]
