import typing

from apps.user_management.constants import (
    AlertGroupTableColumn,
    AlertGroupTableColumns,
    AlertGroupTableColumnTypeChoices,
    AlertGroupTableDefaultColumnChoices,
)

if typing.TYPE_CHECKING:
    from apps.user_management.models import User


def default_columns() -> typing.List[AlertGroupTableColumn]:
    return [
        {"name": column.label, "id": column.value, "type": AlertGroupTableColumnTypeChoices.DEFAULT.value}
        for column in AlertGroupTableDefaultColumnChoices
    ]


def alert_group_table_user_settings(user: "User") -> AlertGroupTableColumns:
    organization_columns = user.organization.alert_group_table_columns
    visible_columns: typing.List[AlertGroupTableColumn]
    if user.alert_groups_table_selected_columns:
        visible_columns = [
            column for column in user.alert_groups_table_selected_columns if column in organization_columns
        ]
    else:
        visible_columns = default_columns()
    user.update_alert_group_table_columns_settings(visible_columns)
    hidden_columns: typing.List[AlertGroupTableColumn] = [
        column for column in organization_columns if column not in visible_columns
    ]
    return {"visible": visible_columns, "hidden": hidden_columns}
