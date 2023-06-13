import datetime
import typing

from rest_framework import serializers

from apps.alerts.models import MaintainableObject


class MaintainableObjectSerializerMixin(serializers.Serializer):
    maintenance_mode = serializers.SerializerMethodField()

    # For some reason maintenance_started_at's format is flaky. Forcing the one listed in docs.
    maintenance_started_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%SZ")
    maintenance_end_at = serializers.SerializerMethodField()

    class Meta:
        """
        Child's Meta should re-use fields and read_only_fields. Please avoid simple overriding.
        """

        fields = [
            "maintenance_mode",
            "maintenance_started_at",
            "maintenance_end_at",
        ]

    def get_maintenance_mode(self, obj: MaintainableObject) -> typing.Optional[str]:
        if obj.get_maintenance_mode_display() is None:
            return None
        return str(obj.get_maintenance_mode_display()).lower()

    def get_maintenance_end_at(self, obj: MaintainableObject) -> typing.Optional[str]:
        if obj.till_maintenance_timestamp is None:
            return None
        return serializers.DateTimeField().to_representation(
            datetime.datetime.fromtimestamp(obj.till_maintenance_timestamp)
        )
