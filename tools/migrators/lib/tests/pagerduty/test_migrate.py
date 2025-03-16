from unittest.mock import call, patch

from lib.pagerduty.migrate import (
    filter_escalation_policies,
    filter_integrations,
    filter_schedules,
    migrate,
)


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


class TestPagerDutyFiltering:
    def setup_method(self):
        self.mock_schedule = {
            "id": "SCHEDULE1",
            "name": "Test Schedule",
            "teams": [{"summary": "Team 1"}],
            "schedule_layers": [
                {
                    "users": [
                        {"user": {"id": "USER1"}},
                        {"user": {"id": "USER2"}},
                    ]
                }
            ],
        }

        self.mock_policy = {
            "id": "POLICY1",
            "name": "Test Policy",
            "teams": [{"summary": "Team 1"}],
            "escalation_rules": [
                {
                    "targets": [
                        {"type": "user", "id": "USER1"},
                        {"type": "user", "id": "USER2"},
                    ]
                }
            ],
        }

        self.mock_integration = {
            "id": "INTEGRATION1",
            "name": "Test Integration",
            "service": {
                "name": "Service 1",
                "teams": [{"summary": "Team 1"}],
            },
        }

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    def test_filter_schedules_by_team(self):
        schedules = [
            self.mock_schedule,
            {**self.mock_schedule, "teams": [{"summary": "Team 2"}]},
        ]
        filtered = filter_schedules(schedules)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "SCHEDULE1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1"])
    def test_filter_schedules_by_users(self):
        schedules = [
            self.mock_schedule,
            {
                **self.mock_schedule,
                "schedule_layers": [{"users": [{"user": {"id": "USER3"}}]}],
            },
        ]
        filtered = filter_schedules(schedules)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "SCHEDULE1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_SCHEDULE_REGEX", "^Test")
    def test_filter_schedules_by_regex(self):
        schedules = [
            self.mock_schedule,
            {**self.mock_schedule, "name": "Production Schedule"},
        ]
        filtered = filter_schedules(schedules)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "SCHEDULE1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    def test_filter_escalation_policies_by_team(self):
        policies = [
            self.mock_policy,
            {**self.mock_policy, "teams": [{"summary": "Team 2"}]},
        ]
        filtered = filter_escalation_policies(policies)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "POLICY1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1"])
    def test_filter_escalation_policies_by_users(self):
        policies = [
            self.mock_policy,
            {
                **self.mock_policy,
                "escalation_rules": [{"targets": [{"type": "user", "id": "USER3"}]}],
            },
        ]
        filtered = filter_escalation_policies(policies)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "POLICY1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX", "^Test")
    def test_filter_escalation_policies_by_regex(self):
        policies = [
            self.mock_policy,
            {**self.mock_policy, "name": "Production Policy"},
        ]
        filtered = filter_escalation_policies(policies)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "POLICY1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    def test_filter_integrations_by_team(self):
        integrations = [
            self.mock_integration,
            {
                **self.mock_integration,
                "service": {"teams": [{"summary": "Team 2"}]},
            },
        ]
        filtered = filter_integrations(integrations)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "INTEGRATION1"

    @patch(
        "lib.pagerduty.migrate.PAGERDUTY_FILTER_INTEGRATION_REGEX", "^Service 1 - Test"
    )
    def test_filter_integrations_by_regex(self):
        integrations = [
            self.mock_integration,
            {
                **self.mock_integration,
                "service": {"name": "Service 2"},
                "name": "Production Integration",
            },
        ]
        filtered = filter_integrations(integrations)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "INTEGRATION1"


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

        # Run migration
        migrate()

        # Verify filters were called with correct data
        mock_filter_schedules.assert_called_once_with([{"id": "S1"}])
        mock_filter_policies.assert_called_once_with([{"id": "P1"}])
        mock_filter_integrations.assert_called_once()  # Service data is transformed, so just check it was called

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
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
            [{"id": "U1", "name": "Test User", "email": "test@example.com"}],  # users
            [{"id": "S1", "teams": [{"summary": "Team 1"}]}],  # schedules
            [{"id": "P1", "teams": [{"summary": "Team 1"}]}],  # policies
            [
                {"id": "SVC1", "teams": [{"summary": "Team 1"}], "integrations": []}
            ],  # services with params
            [
                {"id": "SVC1", "teams": [{"summary": "Team 1"}], "integrations": []}
            ],  # services
            [{"id": "V1"}],  # vendors
            [{"id": "BS1", "teams": [{"summary": "Team 1"}]}],  # business services
        ]
        mock_session.jget.return_value = {"overrides": []}  # Mock schedule overrides
        mock_oncall_client = MockOnCallAPIClient.return_value
        mock_oncall_client.list_all.return_value = []

        # Run migration
        migrate()

        # Verify filters were called and filtered by team
        mock_filter_schedules.assert_called_once()
        mock_filter_policies.assert_called_once()
        mock_filter_integrations.assert_called_once()

        # Verify team parameter was included in API calls
        assert mock_session.list_all.call_args_list == [
            call("users", params={"include[]": "notification_rules"}),
            call(
                "schedules",
                params={"include[]": ["schedule_layers", "teams"], "time_zone": "UTC"},
            ),
            call("escalation_policies", params={"include[]": "teams"}),
            call("services", params={"include[]": ["integrations", "teams"]}),
            call("vendors"),
        ]

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
            [{"id": "U1", "name": "Test User", "email": "test@example.com"}],  # users
            [
                {
                    "id": "S1",
                    "schedule_layers": [{"users": [{"user": {"id": "USER1"}}]}],
                }
            ],  # schedules
            [
                {
                    "id": "P1",
                    "escalation_rules": [
                        {"targets": [{"type": "user", "id": "USER1"}]}
                    ],
                }
            ],  # policies
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

        # Run migration
        migrate()

        # Verify filters were called and filtered by users
        mock_filter_schedules.assert_called_once()
        mock_filter_policies.assert_called_once()
        mock_filter_integrations.assert_called_once()
