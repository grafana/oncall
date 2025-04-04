from unittest.mock import call, patch

from lib.opsgenie.resources.notification_rules import migrate_notification_rules


@patch("lib.opsgenie.resources.notification_rules.OnCallAPIClient")
@patch(
    "lib.opsgenie.resources.notification_rules.PRESERVE_EXISTING_USER_NOTIFICATION_RULES",
    False,
)
def test_migrate_notification_rules(mock_client):
    user = {
        "id": "u1",
        "username": "test.user@example.com",
        "notification_rules": [
            {
                "enabled": True,
                "contact": {"method": "sms"},
                "sendAfter": {"timeAmount": 5, "timeUnit": "minutes"},
            },
            {
                "enabled": True,
                "contact": {"method": "voice"},
                "sendAfter": {"timeAmount": 10, "timeUnit": "minutes"},
            },
            {
                "enabled": True,
                "contact": {"method": "mobile"},
                "sendAfter": {"timeAmount": 0, "timeUnit": "minutes"},
            },
        ],
        "oncall_user": {
            "id": "ou1",
            "notification_rules": [{"id": "nr_old"}],
        },
    }

    migrate_notification_rules(user)

    # Verify old rules deletion
    mock_client.delete.assert_called_once_with("personal_notification_rules/nr_old")

    # Verify new rules creation
    assert mock_client.create.call_count == 10
    mock_client.create.assert_has_calls(
        [
            # Non-important notifications (sorted by sendAfter time)
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_mobile_app",
                    "important": False,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "wait",
                    "duration": 300,  # 5 minutes in seconds
                    "important": False,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_sms",
                    "important": False,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "wait",
                    "duration": 300,  # 5 minutes in seconds
                    "important": False,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_phone_call",
                    "important": False,
                },
            ),
            # Important notifications (sorted by sendAfter time)
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_mobile_app_critical",
                    "important": True,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "wait",
                    "duration": 300,  # 5 minutes in seconds
                    "important": True,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_sms",
                    "important": True,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "wait",
                    "duration": 300,  # 5 minutes in seconds
                    "important": True,
                },
            ),
            call(
                "personal_notification_rules",
                {
                    "user_id": "ou1",
                    "type": "notify_by_phone_call",
                    "important": True,
                },
            ),
        ],
        any_order=False,  # Order matters
    )
