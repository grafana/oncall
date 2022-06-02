from rest_framework import serializers

from apps.slack.models import SlackUserIdentity
from apps.user_management.models import User
from common.api_helpers.mixins import EagerLoadingMixin
from common.constants.role import Role


class SlackUserIdentitySerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="slack_id")
    team_id = serializers.CharField(source="slack_team_identity.slack_id")

    class Meta:
        model = SlackUserIdentity
        fields = (
            "user_id",
            "team_id",
        )


class UserSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    id = serializers.ReadOnlyField(read_only=True, source="public_primary_key")
    email = serializers.EmailField(read_only=True)
    role = serializers.SerializerMethodField()
    slack = SlackUserIdentitySerializer(read_only=True, source="slack_user_identity")

    SELECT_RELATED = [
        "slack_user_identity",
        "slack_user_identity__slack_team_identity",
    ]

    class Meta:
        model = User
        fields = ["id", "email", "slack", "username", "role"]

    @staticmethod
    def get_role(obj):
        return Role(obj.role).name.lower()
