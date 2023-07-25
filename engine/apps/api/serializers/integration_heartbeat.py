import humanize
from django.utils import timezone
from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel
from apps.heartbeat.models import IntegrationHeartBeat
from common.api_helpers.custom_fields import OrganizationFilteredPrimaryKeyRelatedField
from common.api_helpers.mixins import EagerLoadingMixin


class IntegrationHeartBeatSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    alert_receive_channel = OrganizationFilteredPrimaryKeyRelatedField(queryset=AlertReceiveChannel.objects)
    timeout_seconds = serializers.ChoiceField(
        allow_null=False,
        required=True,
        choices=IntegrationHeartBeat.TIMEOUT_CHOICES,
    )
    last_heartbeat_time_verbal = serializers.SerializerMethodField()
    instruction = serializers.SerializerMethodField()

    SELECT_RELATED = ["alert_receive_channel"]

    class Meta:
        model = IntegrationHeartBeat
        fields = [
            "id",
            "timeout_seconds",
            "alert_receive_channel",
            "link",
            "last_heartbeat_time_verbal",
            "status",
            "instruction",
        ]

    def validate_alert_receive_channel(self, alert_receive_channel):
        if alert_receive_channel.is_available_for_integration_heartbeat:
            return alert_receive_channel
        else:
            raise serializers.ValidationError(
                {"alert_receive_channel": "Heartbeat is not available for this integration"}
            )

    def get_last_heartbeat_time_verbal(self, obj):
        return self._last_heartbeat_time_verbal(obj) if obj.last_heartbeat_time else None

    def get_instruction(self, obj):
        # Deprecated. Kept for API backward compatibility.
        return ""

    @staticmethod
    def _last_heartbeat_time_verbal(instance):
        """
        This method simplifies testing.
        To compare expected_payload with response.json() it is needed to calculate "now" same way in test and serializer.
        It is easier to implement separate method and mock in tests.
        """
        now = timezone.now()
        return humanize.naturaldelta(now - instance.last_heartbeat_time)
