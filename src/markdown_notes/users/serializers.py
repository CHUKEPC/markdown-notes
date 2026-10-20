"""Serializers for user registration, authentication, and profiles."""

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from markdown_notes.users.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    """Serializer for displaying basic user details."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "avatar_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserRegistrationSerializer(serializers.ModelSerializer[User]):
    """Serializer for registering new user accounts."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "bio",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate password matching and password complexity."""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )

        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create a new user with hashed password."""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            bio=validated_data.get("bio", ""),
        )
        return user


class UserLoginSerializer(serializers.Serializer[dict[str, Any]]):
    """Serializer for authenticating users via username and password."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Authenticate user against provided credentials."""
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Unable to log in with provided credentials."]}
            )
        if not user.is_active:
            raise serializers.ValidationError({"non_field_errors": ["User account is disabled."]})

        attrs["user"] = user
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer[User]):
    """Serializer for updating user profile fields."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "bio",
            "avatar_url",
        ]
