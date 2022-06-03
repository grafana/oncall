from rest_framework import serializers

from apps.alerts.models import AlertGroup, ResolutionNote
from apps.alerts.tasks import invalidate_web_cache_for_alert_group
from apps.api.serializers.user import FastUserSerializer
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin


class ResolutionNoteSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_group = OrganizationFilteredPrimaryKeyRelatedField(
        filter_field="channel__organization",
        queryset=AlertGroup.unarchived_objects,
    )
    text = serializers.CharField(allow_null=False, source="message_text")
    author = FastUserSerializer(read_only=True)

    SELECT_RELATED = ["resolution_note_slack_message", "author"]

    class Meta:
        model = ResolutionNote
        fields = [
            "id",
            "alert_group",
            "source",
            "author",
            "created_at",
            "text",
        ]
        read_only_fields = [
            "author",
            "created_at",
            "source",
        ]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["source"] = ResolutionNote.Source.WEB
        created_instance = super().create(validated_data)
        # Invalidate alert group cache because resolution notes shown in alert group's timeline
        created_instance.alert_group.drop_cached_after_resolve_report_json()
        invalidate_web_cache_for_alert_group(alert_group_pk=created_instance.alert_group.pk)
        return created_instance

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["text"] = instance.text
        result["source"] = {"id": instance.source, "display_name": instance.get_source_display()}
        return result


class ResolutionNoteUpdateSerializer(ResolutionNoteSerializer):
    alert_group = OrganizationFilteredPrimaryKeyRelatedField(read_only=True)

    def update(self, instance, validated_data):
        if instance.source != ResolutionNote.Source.WEB:
            raise BadRequest(detail="Cannot update message with this source type")
        updated_instance = super().update(instance, validated_data)
        # Invalidate alert group cache because resolution notes shown in alert group's timeline
        updated_instance.alert_group.drop_cached_after_resolve_report_json()
        invalidate_web_cache_for_alert_group(alert_group_pk=updated_instance.alert_group.pk)
        return updated_instance
