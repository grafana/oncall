from rest_framework import serializers


class DemoAlertSerializer(serializers.Serializer):
    payload = serializers.JSONField(allow_null=True, required=False)
