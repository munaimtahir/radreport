from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source="content_type.app_label", read_only=True)
    model = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = Permission
        fields = ("id", "name", "codename", "content_type", "app_label", "model")


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, required=False
    )

    class Meta:
        model = Group
        fields = ("id", "name", "permissions")


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )
    user_permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True, required=False
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "password",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", [])
        permissions = validated_data.pop("user_permissions", [])
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        if groups:
            user.groups.set(groups)
        if permissions:
            user.user_permissions.set(permissions)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", None)
        permissions = validated_data.pop("user_permissions", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password is not None and password != "":
            instance.set_password(password)

        instance.save()

        if groups is not None:
            instance.groups.set(groups)
        if permissions is not None:
            instance.user_permissions.set(permissions)

        return instance


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = (
        User.objects.all()
        .order_by("username")
        .prefetch_related("groups", "user_permissions")
    )
    permission_classes = [IsAdminUser]
    search_fields = ("username", "email", "first_name", "last_name")
    filterset_fields = ("is_active", "is_staff", "is_superuser", "groups")

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        password = request.data.get("password")
        if not password:
            return Response(
                {"detail": "Password is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = self.get_object()
        user.set_password(password)
        user.save()
        return Response({"detail": "Password updated"}, status=status.HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all().order_by("name").prefetch_related("permissions")
    permission_classes = [IsAdminUser]
    search_fields = ("name",)
    filterset_fields = ("name",)

    @action(detail=False, methods=["get"], url_path="standard-roles")
    def standard_roles(self, request):
        """Return the standard roles used across the app (no mutation)."""
        # Align with existing desk roles and seeds (seed_roles_phase3)
        roles = [
            {"name": "registration", "description": "Front-desk registration desk users"},
            {"name": "performance", "description": "Performing/tech users handling studies"},
            {"name": "verification", "description": "Verification/consultant reviewers"},
            {"name": "admin", "description": "Superuser-equivalent; manage settings/templates"},
        ]
        # Flag which exist already
        existing = set(Group.objects.values_list("name", flat=True))
        for r in roles:
            r["exists"] = r["name"] in existing
        return Response(roles)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PermissionSerializer
    queryset = Permission.objects.all().order_by("content_type__app_label", "codename")
    permission_classes = [IsAdminUser]
    search_fields = ("name", "codename", "content_type__app_label")
