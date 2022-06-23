from rest_framework import serializers

from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "title",
            "message",
            "image_url",
            "link_to_upstream_details",
            "render_for_web",
            "created_at",
        ]
