from rest_framework import serializers

from apps.user_management.models import Organization


class OrganizationSlackSettingsSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Organization
        fields = [
            "pk",
            "acknowledge_remind_timeout",
            "unacknowledge_timeout",
        ]

    def update(self, instance, validated_data):
        if validated_data.get("acknowledge_remind_timeout") == 0:
            validated_data["unacknowledge_timeout"] = 0
        return super().update(instance, validated_data)
