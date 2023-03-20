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
            "critical_notification_sound_name",
            "critical_notification_volume_type",
            "critical_notification_volume",
            "critical_notification_override_dnd",
        )
