from rest_framework import serializers

from apps.mobile_app.models import MobileAppUserSettings


class MobileAppUserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileAppUserSettings
        fields = (
            "default_notification_sound_name",
            "default_notification_volume_type",
            "default_notification_volume",
            "default_notification_volume_override",
            "important_notification_sound_name",
            "important_notification_volume_type",
            "important_notification_volume",
            "important_notification_override_dnd",
            "info_notifications_enabled",
            "going_oncall_notification_timing",
        )
