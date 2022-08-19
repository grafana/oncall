from rest_framework import serializers

from apps.alerts.incident_appearance.renderers.web_renderer import AlertWebRenderer
from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    render_for_web = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "link_to_upstream_details",
            "render_for_web",
            "created_at",
        ]

    def get_render_for_web(self, obj):
        return AlertWebRenderer(obj).render()


class AlertRawSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Alert
        fields = [
            "id",
            "raw_request_data",
        ]
