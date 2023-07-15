from rest_framework import serializers

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault


class ActionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team_id = TeamPrimaryKeyRelatedField(required=False, allow_null=True, source="team")
    url = serializers.CharField(required=True, allow_null=False, allow_blank=False, source="webhook")

    class Meta:
        model = CustomButton
        fields = [
            "id",
            "name",
            "organization",
            "team_id",
            "url",
            "data",
            "user",
            "password",
            "authorization_header",
            "forward_whole_payload",
        ]
