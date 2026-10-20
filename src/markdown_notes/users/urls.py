"""URL routing for user authentication and profile endpoints."""

from django.urls import path

from markdown_notes.users.views import LoginView, LogoutView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("me/", ProfileView.as_view(), name="user-profile"),
]
