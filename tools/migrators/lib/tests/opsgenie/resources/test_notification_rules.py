from unittest.mock import patch

from lib.opsgenie.resources.notification_rules import migrate_notification_rules


@patch("lib.opsgenie.resources.notification_rules.OnCallAPIClient")
def test_migrate_notification_rules(mock_client):
    user = {
        "id": "u1",
        "username": "test.user@example.com",
        "notification_rules": [
            {
                "enabled": True,
                "contact": {"method": "sms"},
                "sendAfter": {
                    "timeAmount": 5,
                    "timeUnit": "minutes"
                },
                "criteria": {"isHighPriority": True},
            },
            {
                "enabled": True,
                "contact": {"method": "voice"},
                "sendAfter": {
                    "timeAmount": 10,
                    "timeUnit": "minutes"
                },
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
    mock_client.create.assert_any_call(
        "personal_notification_rules",
        {
            "user_id": "ou1",
            "type": "notify_by_sms",
            "important": True,
            "duration": 300,  # 5 minutes in seconds
        },
    )

    mock_client.create.assert_any_call(
        "personal_notification_rules",
        {
            "user_id": "ou1",
            "type": "notify_by_phone_call",
            "important": False,
            "duration": 600,  # 10 minutes in seconds
        },
    )
