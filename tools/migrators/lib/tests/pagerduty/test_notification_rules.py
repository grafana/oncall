import os
from unittest.mock import call, patch

# Mock environment variables before importing any modules that use them
os.environ["MIGRATING_FROM"] = "pagerduty"
os.environ["ONCALL_API_TOKEN"] = "test-token"
os.environ["ONCALL_API_URL"] = "http://test"
os.environ["PAGERDUTY_API_TOKEN"] = "test-pd-token"
os.environ["MODE"] = "plan"

from lib.pagerduty.resources.notification_rules import migrate_notification_rules


class TestNotificationRulesMigration:
    def setup_method(self):
        self.pd_user = {
            "id": "U1",
            "name": "Test User",
            "email": "test@example.com",
            "notification_rules": [{
                "id": "PD1",
                "urgency": "high",
                "start_delay_in_minutes": 0,
                "contact_method": {
                    "type": "email_contact_method"
                }
            }]
        }
        self.oncall_user = {
            "id": "OC1",
            "email": "test@example.com",
            "notification_rules": []
        }
        self.pd_user["oncall_user"] = self.oncall_user

    @patch("lib.pagerduty.resources.notification_rules.PRESERVE_EXISTING_NOTIFICATION_POLICIES", True)
    @patch("lib.pagerduty.resources.notification_rules.OnCallAPIClient")
    def test_existing_notification_policies_are_preserved(self, MockOnCallAPIClient):
        # Setup user with existing notification rules
        self.oncall_user["notification_rules"] = [{"id": "NR1"}]

        # Run migration
        migrate_notification_rules(self.pd_user)

        # Verify no notification rules were migrated
        MockOnCallAPIClient.create.assert_not_called()

    @patch("lib.pagerduty.resources.notification_rules.PRESERVE_EXISTING_NOTIFICATION_POLICIES", True)
    @patch("lib.pagerduty.resources.notification_rules.OnCallAPIClient")
    def test_notification_policies_migrated_when_none_exist(self, MockOnCallAPIClient):
        # Run migration
        migrate_notification_rules(self.pd_user)

        # Verify notification rules were migrated for both important and non-important cases
        expected_calls = [
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": False
            }),
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": True
            })
        ]
        MockOnCallAPIClient.create.assert_has_calls(expected_calls)

    @patch("lib.pagerduty.resources.notification_rules.PRESERVE_EXISTING_NOTIFICATION_POLICIES", False)
    @patch("lib.pagerduty.resources.notification_rules.OnCallAPIClient")
    def test_existing_notification_policies_are_replaced_when_preserve_is_false(self, MockOnCallAPIClient):
        # Setup user with existing notification rules
        self.oncall_user["notification_rules"] = [
            {"id": "NR1", "important": False},
            {"id": "NR2", "important": True}
        ]

        # Run migration
        migrate_notification_rules(self.pd_user)

        # Verify old rules were deleted
        expected_delete_calls = [
            call("personal_notification_rules/NR1"),
            call("personal_notification_rules/NR2")
        ]
        MockOnCallAPIClient.delete.assert_has_calls(expected_delete_calls, any_order=True)

        # Verify new rules were created
        expected_create_calls = [
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": False
            }),
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": True
            })
        ]
        MockOnCallAPIClient.create.assert_has_calls(expected_create_calls)

    @patch("lib.pagerduty.resources.notification_rules.PRESERVE_EXISTING_NOTIFICATION_POLICIES", False)
    @patch("lib.pagerduty.resources.notification_rules.OnCallAPIClient")
    def test_notification_policies_migrated_when_none_exist_and_preserve_is_false(self, MockOnCallAPIClient):
        # Run migration
        migrate_notification_rules(self.pd_user)

        # Verify no rules were deleted (since none existed)
        MockOnCallAPIClient.delete.assert_not_called()

        # Verify new rules were created
        expected_create_calls = [
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": False
            }),
            call("personal_notification_rules", {
                "user_id": "OC1",
                "type": "notify_by_email",
                "important": True
            })
        ]
        MockOnCallAPIClient.create.assert_has_calls(expected_create_calls)
