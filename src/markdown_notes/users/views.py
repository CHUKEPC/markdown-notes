"""Views for user registration, authentication, and profile management."""

from typing import Any

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from markdown_notes.users.models import User
from markdown_notes.users.serializers import (
    UserLoginSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """Register a new user account and return an authentication token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Handle user registration request."""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate or retrieve authentication token for the newly created user
        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data

        return Response(
            {
                "message": "User registered successfully.",
                "token": token.key,
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a user and return their authentication token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Handle user login request."""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data

        return Response(
            {
                "message": "Login successful.",
                "token": token.key,
                "user": user_data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Log out a user by deleting their authentication token."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Delete active authentication token for current user."""
        assert isinstance(request.user, User)
        Token.objects.filter(user=request.user).delete()
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveUpdateAPIView[User]):
    """Retrieve or update profile details for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self) -> type[UserSerializer | UserProfileUpdateSerializer]:
        """Use distinct serializers for retrieve and update operations."""
        if self.request.method in ("PUT", "PATCH"):
            return UserProfileUpdateSerializer
        return UserSerializer

    def get_object(self) -> User:
        """Return the authenticated user as the target object."""
        return self.request.user  # type: ignore[return-value]

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Return authenticated user profile data."""
        instance = self.get_object()
        serializer = UserSerializer(instance)
        return Response(serializer.data)
