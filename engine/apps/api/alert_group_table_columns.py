import typing

from apps.user_management.constants import default_columns
from apps.user_management.types import AlertGroupTableColumns

if typing.TYPE_CHECKING:
    from apps.user_management.models import User


def alert_group_table_user_settings(user: "User") -> AlertGroupTableColumns:
    """
    Returns user settings for alert group table columns. The flag "default" shows that user has default settings for
    visible columns. It's used by frontend to enable/disable `reset` button.
    This function uses lazy update to update columns settings for organization and for user.
    """
    default_organization_columns = default_columns()
    if not user.organization.alert_group_table_columns:
        user.organization.update_alert_group_table_columns(default_organization_columns)
    organization_columns = user.organization.alert_group_table_columns
    if user.alert_group_table_selected_columns:
        visible_columns = [
            column for column in user.alert_group_table_selected_columns if column in organization_columns
        ]
    else:
        visible_columns = default_organization_columns
    user.update_alert_group_table_selected_columns(visible_columns)
    hidden_columns = [column for column in organization_columns if column not in visible_columns]
    return {
        "visible": visible_columns,
        "hidden": hidden_columns,
        "default": visible_columns == default_organization_columns,
    }
