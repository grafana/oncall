from rest_framework import serializers

from apps.mobile_app.models import MobileAppUserSettings
from common.api_helpers.custom_fields import TimeZoneField


class MobileAppUserSettingsSerializer(serializers.ModelSerializer):
    time_zone = TimeZoneField(required=False, allow_null=False)

    class Meta:
        model = MobileAppUserSettings
        fields = (
            "info_notification_sound_name",
            "info_notification_volume_type",
            "info_notification_volume",
            "info_notification_volume_override",
            "default_notification_sound_name",
            "default_notification_volume_type",
            "default_notification_volume",
            "default_notification_volume_override",
            "important_notification_sound_name",
            "important_notification_volume_type",
            "important_notification_volume",
            "important_notification_volume_override",
            "important_notification_override_dnd",
            "info_notifications_enabled",
            "going_oncall_notification_timing",
            "locale",
            "time_zone",
        )
