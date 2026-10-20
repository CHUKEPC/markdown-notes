"""Root URL configuration for markdown_notes project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("markdown_notes.users.urls")),
    path("api/", include("markdown_notes.notes.urls")),
]
