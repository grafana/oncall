from unittest.mock import call, patch

from lib.oncall.api_client import OnCallAPIClient
from lib.pagerduty.resources.notification_rules import migrate_notification_rules


@patch.object(OnCallAPIClient, "delete")
@patch.object(OnCallAPIClient, "create")
def test_migrate_notification_rules(api_client_create_mock, api_client_delete_mock):
    migrate_notification_rules(
        {
            "notification_rules": [
                {
                    "contact_method": {"type": "sms_contact_method"},
                    "start_delay_in_minutes": 0,
                    "urgency": "high",
                },
                {
                    "contact_method": {"type": "push_notification_contact_method"},
                    "start_delay_in_minutes": 5,
                    "urgency": "high",
                },
            ],
            "oncall_user": {
                "id": "EXISTING_USER_ID",
                "notification_rules": [
                    {"id": "EXISTING_RULE_ID_1", "important": False},
                    {"id": "EXISTING_RULE_ID_2", "important": True},
                ],
            },
        }
    )

    assert api_client_create_mock.call_args_list == [
        call(
            "personal_notification_rules",
            {
                "user_id": "EXISTING_USER_ID",
                "type": "notify_by_sms",
                "important": False,
            },
        ),
        call(
            "personal_notification_rules",
            {
                "user_id": "EXISTING_USER_ID",
                "type": "wait",
                "duration": 300,
                "important": False,
            },
        ),
        call(
            "personal_notification_rules",
            {
                "user_id": "EXISTING_USER_ID",
                "type": "notify_by_mobile_app",
                "important": False,
            },
        ),
        call(
            "personal_notification_rules",
            {"user_id": "EXISTING_USER_ID", "type": "notify_by_sms", "important": True},
        ),
        call(
            "personal_notification_rules",
            {
                "user_id": "EXISTING_USER_ID",
                "type": "wait",
                "duration": 300,
                "important": True,
            },
        ),
        call(
            "personal_notification_rules",
            {
                "user_id": "EXISTING_USER_ID",
                "type": "notify_by_mobile_app",
                "important": True,
            },
        ),
    ]
    assert api_client_delete_mock.call_args_list == [
        call("personal_notification_rules/EXISTING_RULE_ID_1"),
        call("personal_notification_rules/EXISTING_RULE_ID_2"),
    ]
