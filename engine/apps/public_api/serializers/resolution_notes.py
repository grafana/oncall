from rest_framework import serializers

from apps.alerts.models import AlertGroup, ResolutionNote
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField, UserIdField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin


class ResolutionNoteSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_group_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=AlertGroup.objects,
        source="alert_group",
        filter_field="channel__organization",
    )
    text = serializers.CharField(allow_null=False, source="message_text")
    source = serializers.CharField(read_only=True, source="get_source_display")
    author = UserIdField(read_only=True)

    class Meta:
        model = ResolutionNote
        fields = [
            "id",
            "alert_group_id",
            "author",
            "source",
            "created_at",
            "text",
        ]
        read_only_fields = [
            "created_at",
        ]

    SELECT_RELATED = ["alert_group", "resolution_note_slack_message", "author"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["source"] = ResolutionNote.Source.WEB
        return super().create(validated_data)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["text"] = instance.text
        return result


class ResolutionNoteUpdateSerializer(ResolutionNoteSerializer):
    alert_group_id = serializers.CharField(read_only=True, source="alert_group.public_primary_key")

    def update(self, instance, validated_data):
        if instance.source != ResolutionNote.Source.WEB:
            raise BadRequest(detail="Cannot update message with this source type")
        return super().update(instance, validated_data)
