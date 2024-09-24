from rest_framework import serializers

from apps.user_management.models import Team


class TeamSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    grafana_id = serializers.IntegerField(read_only=True, source="team_id")

    class Meta:
        model = Team
        fields = [
            "id",
            "grafana_id",
            "name",
            "email",
            "avatar_url",
        ]
