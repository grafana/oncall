from rest_framework import serializers

from apps.base.models import LiveSetting


class LiveSettingSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    value = serializers.JSONField(allow_null=True)

    class Meta:
        model = LiveSetting
        fields = (
            "id",
            "name",
            "description",
            "default_value",
            "value",
            "error",
            "is_secret",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        def hide_secret(value):
            # transform sensitive credentials to ******1234
            prefix = 6 * "*"
            return prefix + value[-4:]

        if instance.is_secret:
            if instance.value:
                ret["value"] = hide_secret(instance.value)

            if instance.default_value:
                ret["default_value"] = hide_secret(instance.default_value)

        return ret
