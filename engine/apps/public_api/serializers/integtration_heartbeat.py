from rest_framework import serializers

from apps.heartbeat.models import IntegrationHeartBeat


class IntegrationHeartBeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationHeartBeat
        fields = [
            "link",
        ]
