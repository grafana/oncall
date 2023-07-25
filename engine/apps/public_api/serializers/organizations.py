from rest_framework import serializers

from apps.user_management.models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(read_only=True, source="public_primary_key")

    class Meta:
        model = Organization
        fields = ["id"]
        read_only_fields = ["id"]
