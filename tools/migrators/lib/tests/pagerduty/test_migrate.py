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
        call(
            "schedules",
            params={"include[]": ["schedule_layers", "teams"], "time_zone": "UTC"},
        ),
        call("escalation_policies", params={"include[]": "teams"}),
        call("services", params={"include[]": ["integrations", "teams"]}),
        call("vendors"),
    ]

    mock_oncall_client.list_users_with_notification_rules.assert_not_called()


# Need to mock PAGERDUTY_FILTER_USERS in both spots because it's
# used in both migrate.py and users.py (and filter_users is imported from users.py)
@patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1", "USER3"])
@patch("lib.pagerduty.resources.users.PAGERDUTY_FILTER_USERS", ["USER1", "USER3"])
@patch("lib.pagerduty.migrate.MIGRATE_USERS", True)
@patch("lib.pagerduty.migrate.MODE", "migrate")  # Skip report generation
@patch("lib.pagerduty.migrate.APISession")
@patch("lib.pagerduty.migrate.OnCallAPIClient")
@patch("lib.pagerduty.migrate.match_user")
def test_only_specified_users_are_processed_when_filter_users_is_set(
    mock_match_user,
    MockOnCallAPIClient,
    MockAPISession,
):
    mock_session = MockAPISession.return_value

    # Create test users with required fields
    users = [
        {
            "id": "USER1",
            "name": "User 1",
            "oncall_user": None,
            "email": "user1@example.com",
        },
        {
            "id": "USER2",
            "name": "User 2",
            "oncall_user": None,
            "email": "user2@example.com",
        },
        {
            "id": "USER3",
            "name": "User 3",
            "oncall_user": None,
            "email": "user3@example.com",
        },
        {
            "id": "USER4",
            "name": "User 4",
            "oncall_user": None,
            "email": "user4@example.com",
        },
    ]

    # Configure mock to return test users for first call, empty lists for other calls
    mock_session.list_all.side_effect = [
        users,  # users
        [],  # schedules
        [],  # escalation_policies
        [],  # services
        [],  # vendors
    ]
    mock_session.jget.return_value = {"overrides": []}

    def set_oncall_user(user, _):
        # Just leave oncall_user as it is (None)
        pass

    mock_match_user.side_effect = set_oncall_user

    migrate()

    # Check that match_user was only called for USER1 and USER3
    assert mock_match_user.call_count == 2
    user_ids = [call_args[0][0]["id"] for call_args in mock_match_user.call_args_list]
    assert set(user_ids) == {"USER1", "USER3"}


class TestPagerDutyMigrationFiltering:
    @patch("lib.pagerduty.migrate.filter_schedules")
    @patch("lib.pagerduty.migrate.filter_escalation_policies")
    @patch("lib.pagerduty.migrate.filter_integrations")
    @patch("lib.pagerduty.migrate.APISession")
    @patch("lib.pagerduty.migrate.OnCallAPIClient")
    @patch("lib.pagerduty.migrate.ServiceModelClient")
    def test_migrate_calls_filters(
        self,
        MockServiceModelClient,
        MockOnCallAPIClient,
        MockAPISession,
        mock_filter_integrations,
        mock_filter_policies,
        mock_filter_schedules,
    ):
        # Setup mock returns
        mock_session = MockAPISession.return_value
        mock_session.list_all.side_effect = [
            [{"id": "U1", "name": "Test User", "email": "test@example.com"}],  # users
            [{"id": "S1"}],  # schedules
            [{"id": "P1"}],  # policies
            [{"id": "SVC1", "integrations": []}],  # services with params
            [{"id": "SVC1", "integrations": []}],  # services
            [{"id": "V1"}],  # vendors
            [{"id": "BS1"}],  # business services
        ]
        mock_session.jget.return_value = {"overrides": []}  # Mock schedule overrides
        mock_oncall_client = MockOnCallAPIClient.return_value
        mock_oncall_client.list_all.return_value = []
        mock_service_client = MockServiceModelClient.return_value
        mock_service_client.get_components.return_value = []

        migrate()

        # Assert filters were called
        mock_filter_schedules.assert_called_once()
        mock_filter_policies.assert_called_once()
        mock_filter_integrations.assert_called_once()

    @patch("lib.pagerduty.config.PAGERDUTY_FILTER_TEAM", "Team 1")
    @patch("lib.pagerduty.migrate.filter_schedules")
    @patch("lib.pagerduty.migrate.filter_escalation_policies")
    @patch("lib.pagerduty.migrate.filter_integrations")
    @patch("lib.pagerduty.migrate.APISession")
    @patch("lib.pagerduty.migrate.OnCallAPIClient")
    def test_migrate_with_team_filter(
        self,
        MockOnCallAPIClient,
        MockAPISession,
        mock_filter_integrations,
        mock_filter_policies,
        mock_filter_schedules,
    ):
        # Setup mock returns
        mock_session = MockAPISession.return_value
        mock_session.list_all.side_effect = [
            [],  # users
            [{"id": "SCHEDULE1", "teams": [{"summary": "Team 1"}]}],  # schedules
            [
                {"id": "POLICY1", "teams": [{"summary": "Team 1"}]},
            ],  # escalation_policies
            [
                {"id": "SVC1", "teams": [{"summary": "Team 1"}], "integrations": []},
            ],  # services with params
            [
                {"id": "SVC1", "teams": [{"summary": "Team 1"}], "integrations": []},
            ],  # services
            [{"id": "V1"}],  # vendors
            [{"id": "BS1", "teams": [{"summary": "Team 1"}]}],  # business services
        ]
        mock_session.jget.return_value = {"overrides": []}
        mock_filter_schedules.return_value = []
        mock_filter_policies.return_value = []
        mock_filter_integrations.return_value = []

        migrate()

        # Assert scheduled were filtered by team
        mock_filter_schedules.assert_called_once()
        mock_filter_policies.assert_called_once()
        mock_filter_integrations.assert_called_once()

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1"])
    @patch("lib.pagerduty.migrate.filter_schedules")
    @patch("lib.pagerduty.migrate.filter_escalation_policies")
    @patch("lib.pagerduty.migrate.filter_integrations")
    @patch("lib.pagerduty.migrate.APISession")
    @patch("lib.pagerduty.migrate.OnCallAPIClient")
    @patch("lib.pagerduty.migrate.ServiceModelClient")
    def test_migrate_with_users_filter(
        self,
        MockServiceModelClient,
        MockOnCallAPIClient,
        MockAPISession,
        mock_filter_integrations,
        mock_filter_policies,
        mock_filter_schedules,
    ):
        # Setup mock returns
        mock_session = MockAPISession.return_value
        mock_session.list_all.side_effect = [
            [],  # users
            [
                {
                    "id": "SCHEDULE1",
                    "schedule_layers": [{"users": [{"user": {"id": "USER1"}}]}],
                }
            ],  # schedules
            [
                {
                    "id": "POLICY1",
                    "escalation_rules": [
                        {"targets": [{"type": "user", "id": "USER1"}]}
                    ],
                }
            ],  # escalation_policies
            [{"id": "SVC1", "integrations": []}],  # services with params
            [{"id": "SVC1", "integrations": []}],  # services
            [{"id": "V1"}],  # vendors
            [{"id": "BS1"}],  # business services
        ]
        mock_session.jget.return_value = {"overrides": []}  # Mock schedule overrides

        mock_filter_schedules.return_value = []
        mock_filter_policies.return_value = []
        mock_filter_integrations.return_value = []

        mock_oncall_client = MockOnCallAPIClient.return_value
        mock_oncall_client.list_all.return_value = []
        mock_service_client = MockServiceModelClient.return_value
        mock_service_client.get_components.return_value = []

        migrate()

        # Assert schedule filter was called with correct parameters
        mock_filter_schedules.assert_called_once()
        mock_filter_policies.assert_called_once()
        mock_filter_integrations.assert_called_once()
