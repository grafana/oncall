import logging

from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertGroupWebRenderer
from apps.alerts.models import Alert, AlertGroup
from apps.api.serializers.alert_group import AlertGroupFieldsCacheSerializerMixin

logger = logging.getLogger(__name__)


class AlertSerializer(serializers.ModelSerializer):
    id_oncall = serializers.CharField(read_only=True, source="public_primary_key")
    payload = serializers.JSONField(read_only=True, source="raw_request_data")

    class Meta:
        model = Alert
        fields = [
            "id_oncall",
            "payload",
        ]


class AlertGroupSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    status = serializers.SerializerMethodField(source="get_status")
    link = serializers.CharField(read_only=True, source="web_link")
    title = serializers.CharField(read_only=True, source="long_verbose_name_without_formatting")
    alerts = AlertSerializer(many=True, read_only=True)

    render_for_web = serializers.SerializerMethodField()

    def get_status(self, obj):
        return next(filter(lambda status: status[0] == obj.status, AlertGroup.STATUS_CHOICES))[1].lower()

    def get_render_for_web(self, obj):
        last_alert = obj.alerts.last()
        if last_alert is None:
            return {}
        return AlertGroupFieldsCacheSerializerMixin.get_or_set_web_template_field(
            obj,
            last_alert,
            AlertGroupFieldsCacheSerializerMixin.RENDER_FOR_WEB_FIELD_NAME,
            AlertGroupWebRenderer,
        )

    class Meta:
        model = AlertGroup
        fields = [
            "id",
            "link",
            "status",
            "alerts",
            "title",
            "render_for_web",
        ]
