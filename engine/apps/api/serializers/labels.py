from rest_framework import serializers

from apps.labels.models import LabelKeyCache, LabelValueCache


class LabelKeySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="key_id")
    repr = serializers.CharField(source="key_repr")

    class Meta:
        model = LabelKeyCache
        fields = (
            "id",
            "repr",
        )


class LabelValueSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="value_id")
    repr = serializers.CharField(source="value_repr")

    class Meta:
        model = LabelValueCache
        fields = (
            "id",
            "repr",
        )


class LabelSerializer(serializers.Serializer):
    key = LabelKeySerializer(source="key_cache")
    value = LabelValueSerializer(source="value_cache")
