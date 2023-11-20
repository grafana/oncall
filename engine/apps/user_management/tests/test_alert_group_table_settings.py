import pytest

from apps.user_management.constants import AlertGroupTableColumnTypeChoices
from apps.user_management.utils import alert_group_table_user_settings, default_columns

DEFAULT_COLUMNS = default_columns()


@pytest.mark.parametrize(
    "user_settings,organization_settings,expected_result",
    [
        # user doesn't have settings, organization has default settings - all columns are visible
        (
            None,
            DEFAULT_COLUMNS,
            {"visible": DEFAULT_COLUMNS, "hidden": []},
        ),
        # user doesn't have settings, organization has updated settings - only default columns are visible
        (
            None,
            DEFAULT_COLUMNS + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            {
                "visible": DEFAULT_COLUMNS,
                "hidden": [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            },
        ),
        # user has settings, organization has default settings - only selected columns are visible
        (
            DEFAULT_COLUMNS[:3],
            DEFAULT_COLUMNS,
            {"visible": DEFAULT_COLUMNS[:3], "hidden": DEFAULT_COLUMNS[3:]},
        ),
        # user has settings, organization has unchanged settings - only selected columns are visible
        (
            DEFAULT_COLUMNS[:3]
            + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            DEFAULT_COLUMNS + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            {
                "visible": (
                    DEFAULT_COLUMNS[:3]
                    + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}]
                ),
                "hidden": DEFAULT_COLUMNS[3:],
            },
        ),
        # user has settings, organization has updated settings - column was removed, remove from settings
        (
            DEFAULT_COLUMNS[:3]
            + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            DEFAULT_COLUMNS,
            {"visible": DEFAULT_COLUMNS[:3], "hidden": DEFAULT_COLUMNS[3:]},
        ),
        # user has settings with reordered columns, organization has unchanged settings - selected columns in particular
        # order are visible
        (
            [
                DEFAULT_COLUMNS[1],
                DEFAULT_COLUMNS[3],
                {"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value},
                DEFAULT_COLUMNS[2],
            ],
            DEFAULT_COLUMNS + [{"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value}],
            {
                "visible": [
                    DEFAULT_COLUMNS[1],
                    DEFAULT_COLUMNS[3],
                    {"name": "Test", "id": "test", "type": AlertGroupTableColumnTypeChoices.LABEL.value},
                    DEFAULT_COLUMNS[2],
                ],
                "hidden": DEFAULT_COLUMNS[:1] + DEFAULT_COLUMNS[4:],
            },
        ),
    ],
)
@pytest.mark.django_db
def test_alert_group_table_user_settings(
    user_settings,
    organization_settings,
    expected_result,
    make_organization_and_user,
):
    organization, user = make_organization_and_user()
    organization.update_alert_group_table_columns(organization_settings)
    if user_settings:
        user.update_alert_group_table_columns_settings(user_settings)
    result = alert_group_table_user_settings(user)
    assert result == expected_result
    assert user.alert_groups_table_selected_columns == result["visible"]
