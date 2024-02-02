from rest_framework import serializers

from apps.api.permissions import LegacyAccessControlRole
from apps.slack.models import SlackUserIdentity
from apps.user_management.models import User
from common.api_helpers.mixins import EagerLoadingMixin


class SlackUserIdentitySerializer(serializers.ModelSerializer):
    user_id: str = serializers.CharField(source="slack_id")
    team_id: str = serializers.CharField(source="slack_team_identity.slack_id")

    class Meta:
        model = SlackUserIdentity
        fields = (
            "user_id",
            "team_id",
        )


class FastUserSerializer(serializers.ModelSerializer):
    id: str = serializers.ReadOnlyField(read_only=True, source="public_primary_key")
    email: str = serializers.EmailField(read_only=True)
    role: str = serializers.SerializerMethodField()  # LEGACY, should be removed eventually
    is_phone_number_verified: bool = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "is_phone_number_verified"]

    @staticmethod
    def get_role(obj: User) -> str:
        """
        LEGACY, should be removed eventually
        """
        return LegacyAccessControlRole(obj.role).name.lower()

    def get_is_phone_number_verified(self, obj: User) -> bool:
        return obj.verified_phone_number is not None


class UserSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    id: str = serializers.ReadOnlyField(read_only=True, source="public_primary_key")
    email: str = serializers.EmailField(read_only=True)
    slack: SlackUserIdentity = SlackUserIdentitySerializer(read_only=True, source="slack_user_identity")
    role: str = serializers.SerializerMethodField()  # LEGACY, should be removed eventually
    is_phone_number_verified: bool = serializers.SerializerMethodField()
    teams: list[str] = serializers.SlugRelatedField(read_only=True, many=True, slug_field="public_primary_key")

    SELECT_RELATED = [
        "slack_user_identity",
        "slack_user_identity__slack_team_identity",
    ]
    PREFETCH_RELATED = ["teams"]

    class Meta:
        model = User
        fields = ["id", "email", "slack", "username", "role", "is_phone_number_verified", "timezone", "teams"]
        read_only_fields = ["timezone"]

    @staticmethod
    def get_role(obj: User) -> str:
        """
        LEGACY, should be removed eventually
        """
        return LegacyAccessControlRole(obj.role).name.lower()

    def get_is_phone_number_verified(self, obj: User) -> bool:
        return obj.verified_phone_number is not None
