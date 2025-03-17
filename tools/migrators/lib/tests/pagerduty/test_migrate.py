from unittest.mock import call, patch

from lib.pagerduty.migrate import (
    filter_escalation_policies,
    filter_integrations,
    filter_schedules,
    filter_users,
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


@patch("lib.pagerduty.migrate.MIGRATE_USERS", True)
@patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1", "USER3"])
@patch("lib.pagerduty.migrate.MODE", "migrate")  # Skip report generation
@patch("lib.pagerduty.migrate.APISession")
@patch("lib.pagerduty.migrate.OnCallAPIClient")
def test_only_specified_users_are_processed_when_filter_users_is_set(
    MockOnCallAPIClient, MockAPISession
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

    # Mock the user matching function to set oncall_user
    with patch("lib.pagerduty.migrate.match_user") as mock_match_user:

        def set_oncall_user(user, _):
            # Just leave oncall_user as it is (None)
            pass

        mock_match_user.side_effect = set_oncall_user

        # Run migrate
        migrate()

        # Check that match_user was only called for USER1 and USER3
        assert mock_match_user.call_count == 2
        user_ids = [
            call_args[0][0]["id"] for call_args in mock_match_user.call_args_list
        ]
        assert set(user_ids) == {"USER1", "USER3"}


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

        self.users = [
            {"id": "USER1", "name": "User 1"},
            {"id": "USER2", "name": "User 2"},
            {"id": "USER3", "name": "User 3"},
        ]

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER1", "USER3"])
    def test_filter_users(self):
        """Test filtering users by ID when PAGERDUTY_FILTER_USERS is set."""
        filtered = filter_users(self.users)
        assert len(filtered) == 2
        assert {u["id"] for u in filtered} == {"USER1", "USER3"}

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", [])
    def test_filter_users_no_filter(self):
        """Test that all users are kept when PAGERDUTY_FILTER_USERS is empty."""
        filtered = filter_users(self.users)
        assert len(filtered) == 3
        assert {u["id"] for u in filtered} == {"USER1", "USER2", "USER3"}

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
            {**self.mock_schedule, "name": "Another Schedule"},
        ]
        filtered = filter_schedules(schedules)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "SCHEDULE1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER3"])
    def test_filter_schedules_with_multiple_filters_or_logic(self):
        """Test that OR logic is applied between filters - a schedule matching any filter is included"""
        schedules = [
            self.mock_schedule,  # Has Team 1 but not USER3
            {
                "id": "SCHEDULE2",
                "name": "Test Schedule 2",
                "teams": [{"summary": "Team 2"}],  # Not Team 1
                "schedule_layers": [
                    {"users": [{"user": {"id": "USER3"}}]}
                ],  # Has USER3
            },
            {
                "id": "SCHEDULE3",
                "name": "Test Schedule 3",
                "teams": [{"summary": "Team 3"}],  # Not Team 1
                "schedule_layers": [
                    {"users": [{"user": {"id": "USER4"}}]}
                ],  # Not USER3
            },
        ]
        filtered = filter_schedules(schedules)
        # SCHEDULE1 matches team filter, SCHEDULE2 matches user filter, SCHEDULE3 matches neither
        assert len(filtered) == 2
        assert {s["id"] for s in filtered} == {"SCHEDULE1", "SCHEDULE2"}

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
                "escalation_rules": [
                    {
                        "targets": [
                            {"type": "user", "id": "USER3"},
                            {"type": "user", "id": "USER4"},
                        ]
                    }
                ],
            },
        ]
        filtered = filter_escalation_policies(policies)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "POLICY1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX", "^Test")
    def test_filter_escalation_policies_by_regex(self):
        policies = [
            self.mock_policy,
            {**self.mock_policy, "name": "Another Policy"},
        ]
        filtered = filter_escalation_policies(policies)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "POLICY1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_USERS", ["USER3"])
    def test_filter_escalation_policies_with_multiple_filters_or_logic(self):
        """Test that OR logic is applied between filters - a policy matching any filter is included"""
        policies = [
            self.mock_policy,  # Has Team 1 but not USER3
            {
                "id": "POLICY2",
                "name": "Test Policy 2",
                "teams": [{"summary": "Team 2"}],  # Not Team 1
                "escalation_rules": [
                    {
                        "targets": [
                            {"type": "user", "id": "USER3"},  # Has USER3
                        ]
                    }
                ],
            },
            {
                "id": "POLICY3",
                "name": "Test Policy 3",
                "teams": [{"summary": "Team 3"}],  # Not Team 1
                "escalation_rules": [
                    {
                        "targets": [
                            {"type": "user", "id": "USER4"},  # Not USER3
                        ]
                    }
                ],
            },
        ]
        filtered = filter_escalation_policies(policies)
        # POLICY1 matches team filter, POLICY2 matches user filter, POLICY3 matches neither
        assert len(filtered) == 2
        assert {p["id"] for p in filtered} == {"POLICY1", "POLICY2"}

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    def test_filter_integrations_by_team(self):
        integrations = [
            self.mock_integration,
            {
                **self.mock_integration,
                "service": {
                    "name": "Service 1",
                    "teams": [{"summary": "Team 2"}],
                },
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
                "service": {"name": "Service 2", "teams": [{"summary": "Team 1"}]},
            },
        ]
        filtered = filter_integrations(integrations)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "INTEGRATION1"

    @patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
    @patch(
        "lib.pagerduty.migrate.PAGERDUTY_FILTER_INTEGRATION_REGEX", "^Service 2 - Test"
    )
    def test_filter_integrations_with_multiple_filters_or_logic(self):
        """Test that OR logic is applied between filters - an integration matching any filter is included"""
        integrations = [
            self.mock_integration,  # Has Team 1 but doesn't match regex
            {
                "id": "INTEGRATION2",
                "name": "Test Integration",
                "service": {
                    "name": "Service 2",  # Matches regex
                    "teams": [{"summary": "Team 2"}],  # Not Team 1
                },
            },
            {
                "id": "INTEGRATION3",
                "name": "Test Integration",
                "service": {
                    "name": "Service 3",  # Doesn't match regex
                    "teams": [{"summary": "Team 3"}],  # Not Team 1
                },
            },
        ]
        filtered = filter_integrations(integrations)
        # INTEGRATION1 matches team filter, INTEGRATION2 matches regex filter, INTEGRATION3 matches neither
        assert len(filtered) == 2
        assert {i["id"] for i in filtered} == {"INTEGRATION1", "INTEGRATION2"}


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


@patch("lib.pagerduty.migrate.VERBOSE_LOGGING", True)
@patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
def test_verbose_logging_for_schedules(capsys):
    schedules = [
        {
            "id": "SCHEDULE1",
            "name": "Test Schedule",
            "teams": [{"summary": "Team 1"}],
        },
        {
            "id": "SCHEDULE2",
            "name": "Other Schedule",
            "teams": [{"summary": "Team 2"}],
        },
    ]

    filter_schedules(schedules)

    # Capture the output and verify verbose messages
    captured = capsys.readouterr()
    assert "Filtered out 1 schedules" in captured.out
    assert "Schedule SCHEDULE2: No teams found for team filter: Team 1" in captured.out


@patch("lib.pagerduty.migrate.VERBOSE_LOGGING", False)
@patch("lib.pagerduty.migrate.PAGERDUTY_FILTER_TEAM", "Team 1")
def test_non_verbose_logging_for_schedules(capsys):
    schedules = [
        {
            "id": "SCHEDULE1",
            "name": "Test Schedule",
            "teams": [{"summary": "Team 1"}],
        },
        {
            "id": "SCHEDULE2",
            "name": "Other Schedule",
            "teams": [{"summary": "Team 2"}],
        },
    ]

    filter_schedules(schedules)

    # Capture the output and verify no verbose messages
    captured = capsys.readouterr()
    assert "Filtered out 1 schedules" in captured.out
    assert "Schedule SCHEDULE2" not in captured.out
