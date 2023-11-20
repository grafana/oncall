from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user_management.constants import AlertGroupTableColumnTypeChoices, AlertGroupTableDefaultColumnChoices


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
        self._validate_id(data)
        return data

    def _validate_id(self, data):
        if (
            data["type"] == AlertGroupTableColumnTypeChoices.DEFAULT.value
            and data["id"] not in AlertGroupTableDefaultColumnChoices.values
        ):
            raise ValidationError("Invalid column id format")


class AlertGroupTableColumnsListSerializer(serializers.Serializer):
    visible = AlertGroupTableColumnSerializer(many=True)
    hidden = AlertGroupTableColumnSerializer(many=True)

    def validate(self, data):
        """
        Validate data regarding if it updates alert group table columns settings for organization or for user
        and validate that at least one column is selected as visible.

        `is_org_settings=True` means that organization alert group table columns list should be updated.
        Validate that all default columns are in the list.

        `is_org_settings=False` means that list of visible columns for user should be updated.
        Validate that all columns exist in organization alert group table columns list.
        """
        is_org_settings = self.context.get("is_org_settings") is True
        organization = self.context["request"].auth.organization
        columns_list = data["visible"] + data["hidden"]
        request_columns_ids = [column["id"] for column in columns_list]
        if len(data["visible"]) == 0:
            raise ValidationError("At least one column should be selected as visible")
        if is_org_settings:
            if not set(request_columns_ids) >= set(AlertGroupTableDefaultColumnChoices.values):
                raise ValidationError("Default column cannot be removed")
            elif len(request_columns_ids) > len(set(request_columns_ids)):
                raise ValidationError("Duplicate column")
        else:
            organization_columns_ids = [column["id"] for column in organization.alert_group_table_columns]
            if set(organization_columns_ids) != set(request_columns_ids):
                raise ValidationError("Invalid settings")
        return data
