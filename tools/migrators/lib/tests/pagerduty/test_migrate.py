from unittest.mock import call, patch

from lib.pagerduty.migrate import migrate


@patch("lib.pagerduty.migrate.MIGRATE_USERS", False)
@patch("lib.pagerduty.migrate.APISession")
@patch("lib.pagerduty.migrate.OnCallAPIClient")
def test_users_are_skipped_when_migrate_users_is_false(
    MockOnCallAPIClient, MockAPISession
):
    mock_session = MockAPISession.return_value
    mock_session.list_all.return_value = []
    mock_oncall_client = MockOnCallAPIClient.return_value

    migrate()

    # Assert no user-related fetching or migration occurs
    assert mock_session.list_all.call_args_list == [
        call("schedules", params={"include[]": "schedule_layers", "time_zone": "UTC"}),
        call("escalation_policies"),
        call("services", params={"include[]": "integrations"}),
        call("vendors"),
        # no user notification rules fetching
    ]

    mock_oncall_client.list_users_with_notification_rules.assert_not_called()
