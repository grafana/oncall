from rest_framework import serializers

from apps.api.permissions import LegacyAccessControlRole
from apps.slack.models import SlackUserIdentity
from apps.user_management.models import User
from common.api_helpers.mixins import EagerLoadingMixin


class SlackUserIdentitySerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="slack_id")
    team_id = serializers.CharField(source="slack_team_identity.slack_id")

    class Meta:
        model = SlackUserIdentity
        fields = (
            "user_id",
            "team_id",
        )


class FastUserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(read_only=True, source="public_primary_key")
    email = serializers.EmailField(read_only=True)
    role = serializers.SerializerMethodField()  # LEGACY, should be removed eventually
    is_phone_number_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "is_phone_number_verified"]

    @staticmethod
    def get_role(obj):
        """
        LEGACY, should be removed eventually
        """
        return LegacyAccessControlRole(obj.role).name.lower()

    def get_is_phone_number_verified(self, obj):
        return obj.verified_phone_number is not None


class UserSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    id = serializers.ReadOnlyField(read_only=True, source="public_primary_key")
    email = serializers.EmailField(read_only=True)
    slack = SlackUserIdentitySerializer(read_only=True, source="slack_user_identity")
    role = serializers.SerializerMethodField()  # LEGACY, should be removed eventually
    is_phone_number_verified = serializers.SerializerMethodField()

    SELECT_RELATED = [
        "slack_user_identity",
        "slack_user_identity__slack_team_identity",
    ]

    class Meta:
        model = User
        fields = ["id", "email", "slack", "username", "role", "is_phone_number_verified"]

    @staticmethod
    def get_role(obj):
        """
        LEGACY, should be removed eventually
        """
        return LegacyAccessControlRole(obj.role).name.lower()

    def get_is_phone_number_verified(self, obj):
        return obj.verified_phone_number is not None
