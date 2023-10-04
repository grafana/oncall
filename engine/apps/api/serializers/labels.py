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


class LabelReprSerializer(serializers.Serializer):
    repr = serializers.CharField()


class LabelsSerializerMixin(serializers.Serializer):
    labels = LabelSerializer(many=True, required=False)

    def validate_labels(self, labels):
        if labels:
            keys = {label["key"]["id"] for label in labels}
            if len(keys) != len(labels):
                raise serializers.ValidationError(detail="Duplicate label key")
        return labels
