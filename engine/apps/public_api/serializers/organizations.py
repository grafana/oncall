from rest_framework import serializers

from apps.user_management.models import Organization

from .maintenance import MaintainableObjectSerializerMixin


class OrganizationSerializer(serializers.ModelSerializer, MaintainableObjectSerializerMixin):
    id = serializers.ReadOnlyField(read_only=True, source="public_primary_key")

    class Meta:
        model = Organization
        fields = MaintainableObjectSerializerMixin.Meta.fields + [
            "id",
        ]
        read_only_fields = MaintainableObjectSerializerMixin.Meta.fields + [
            "id",
        ]
