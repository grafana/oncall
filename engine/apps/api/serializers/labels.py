from rest_framework import serializers

from apps.labels.models import Label


class LabelSerializer(serializers.ModelSerializer):
    key_id = serializers.CharField(read_only=True)
    value_id = serializers.CharField(read_only=True)

    class Meta:
        model = Label
        fields = (
            "key_id",
            "value_id",
        )


class LabelParamsSerializer(serializers.Serializer):
    id = serializers.CharField()
    repr = serializers.CharField()


class LabelDataSerializer(serializers.Serializer):
    key = LabelParamsSerializer()
    value = LabelParamsSerializer()
