from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user_management.constants import AlertGroupTableColumnChoices, AlertGroupTableColumnTypeChoices


class ColumnIdField(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if isinstance(data, int) or isinstance(data, str):
            return data
        else:
            raise ValidationError("Invalid column id format")


class AlertGroupTableColumnSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    id = ColumnIdField()
    type = serializers.ChoiceField(choices=AlertGroupTableColumnTypeChoices.choices)

    def validate(self, data):
        # todo: check if id for default is int and for label is str
        # todo: check if every column exists in organization columns list if not is_org_settings
        return data

    def _validate_id(self, column_id, column_type):
        # todo
        if (
            column_type == AlertGroupTableColumnTypeChoices.DEFAULT.value
            and column_id not in AlertGroupTableColumnChoices.values
        ):
            raise ValidationError("Invalid column id format")


class AlertGroupTableColumnsListSerializer(serializers.Serializer):
    visible = AlertGroupTableColumnSerializer(many=True)
    hidden = AlertGroupTableColumnSerializer(many=True)

    def is_org_settings(self):  # todo
        return self.context.get("is_org_settings") is True

    def validate(self, data):
        # todo: check columns list if not is_org_settings (should be the same)
        # todo: check if all default columns are in the list if is_org_settings
        # todo: minimum one columns should be visible
        return data
