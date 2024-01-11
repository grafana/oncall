from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user_management.constants import (
    AlertGroupTableColumnTypeChoices,
    AlertGroupTableDefaultColumnChoices,
    default_columns,
)


class AlertGroupTableColumnSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    id = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(choices=AlertGroupTableColumnTypeChoices.choices)

    def validate(self, data):
        self._validate_id(data)
        return data

    def _validate_id(self, data):
        """Validate if `id` of column with `default` type is in the list of available default columns"""
        if (
            data["type"] == AlertGroupTableColumnTypeChoices.DEFAULT.value
            and data["id"] not in AlertGroupTableDefaultColumnChoices.values
        ):
            raise ValidationError("Invalid column id format")


class AlertGroupTableColumnsOrganizationSerializer(serializers.Serializer):
    visible = AlertGroupTableColumnSerializer(many=True)
    hidden = AlertGroupTableColumnSerializer(many=True)

    def validate(self, data):
        """
        Validate that at least one column is selected as visible and that all default columns are in the list.
        """
        request_columns_by_type = {}
        for column in data["visible"] + data["hidden"]:
            request_columns_by_type.setdefault(column["type"], []).append(column["id"])
        if len(data["visible"]) == 0:
            raise ValidationError("At least one column should be selected as visible")
        elif not (
            set(request_columns_by_type[AlertGroupTableColumnTypeChoices.DEFAULT])
            == set(AlertGroupTableDefaultColumnChoices.values)
        ):
            raise ValidationError("Default column cannot be removed")
        for columns_ids in request_columns_by_type.values():
            if len(columns_ids) > len(set(columns_ids)):
                raise ValidationError("Duplicate column")
        return data


class AlertGroupTableColumnsUserSerializer(AlertGroupTableColumnsOrganizationSerializer):
    def validate(self, data):
        """
        Validate that all columns exist in organization alert group table columns list.
        """
        data = super().validate(data)
        columns = data["visible"] + data["hidden"]
        request_columns_ids = [column["id"] for column in columns]
        organization_columns = self.context["request"].auth.organization.alert_group_table_columns or default_columns()
        organization_columns_ids = [column["id"] for column in organization_columns]
        if set(organization_columns_ids) != set(request_columns_ids):
            raise ValidationError("Invalid settings")
        return data
