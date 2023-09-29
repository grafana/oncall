from rest_framework import serializers

from apps.labels.models import LabelKeyCache, LabelValueCache


class LabelKeySerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = LabelKeyCache
        fields = (
            "id",
            "repr",
        )


class LabelValueSerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = LabelValueCache
        fields = (
            "id",
            "repr",
        )


class LabelSerializer(serializers.Serializer):
    key = LabelKeySerializer()
    value = LabelValueSerializer()


class LabelKeyValuesSerializer(serializers.Serializer):
    key = LabelKeySerializer()
    values = LabelValueSerializer(many=True)
