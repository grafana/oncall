from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.alerts.constants import ServiceNowEmptyMapping

SERVICENOW_PASSWORD_PLACEHOLDER = "**********"


def validate_state(value):
    if len(value) != 2:
        raise ValidationError(["Invalid data"])
    elif not (isinstance(value[0], int) and isinstance(value[1], str)):
        raise ValidationError(["Invalid data"])
    return value


class ServiceNowStateMappingSerializer(serializers.Serializer):
    firing = serializers.ListField(allow_null=True, allow_empty=False, validators=[validate_state])
    acknowledged = serializers.ListField(allow_null=True, allow_empty=False, validators=[validate_state])
    resolved = serializers.ListField(allow_null=True, allow_empty=False, validators=[validate_state])
    silenced = serializers.ListField(allow_null=True, allow_empty=False, validators=[validate_state])


class AlertReceiveChannelServiceNowSettingsSerializer(serializers.Serializer):
    instance_url = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()
    state_mapping = ServiceNowStateMappingSerializer(default=ServiceNowEmptyMapping)
    is_configured = serializers.BooleanField(default=False)
