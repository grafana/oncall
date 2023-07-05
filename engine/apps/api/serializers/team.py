from rest_framework import serializers

from apps.user_management.models import Team


class TeamSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Team
        fields = (
            "id",
            "name",
            "email",
            "avatar_url",
            "is_sharing_resources_to_all",
        )

        read_only_fields = [
            "id",
            "name",
            "email",
            "avatar_url",
        ]
