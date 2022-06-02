from rest_framework import serializers

from apps.alerts.models import CustomButton
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField


class ActionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    team_id = TeamPrimaryKeyRelatedField(allow_null=True, source="team")

    class Meta:
        model = CustomButton
        fields = [
            "id",
            "name",
            "team_id",
        ]
