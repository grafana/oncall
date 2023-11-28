import typing

from apps.user_management.constants import AlertGroupTableColumns, default_columns

if typing.TYPE_CHECKING:
    from apps.user_management.models import User


def alert_group_table_user_settings(user: "User") -> AlertGroupTableColumns:
    """
    Returns user settings for alert group table columns.
    This function uses lazy update to update columns settings for organization and for user.
    """
    if not user.organization.alert_group_table_columns:
        user.organization.update_alert_group_table_columns(default_columns())
    organization_columns = user.organization.alert_group_table_columns
    if user.alert_group_table_selected_columns:
        visible_columns = [
            column for column in user.alert_group_table_selected_columns if column in organization_columns
        ]
    else:
        visible_columns = default_columns()
    user.update_alert_group_table_selected_columns(visible_columns)
    hidden_columns = [column for column in organization_columns if column not in visible_columns]
    return {"visible": visible_columns, "hidden": hidden_columns}
