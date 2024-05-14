from unittest import mock

import pytest

from lib.splunk.resources.paging_policies import migrate_paging_policies

ONCALL_USER_ID = "UABCD12345"
ONCALL_NOTIFICATION_POLICY_ID = "UNP12345"


def _generate_splunk_paging_policy(order: int, contactType: str, timeout: int):
    return {
        "order": order,
        "timeout": timeout,
        "contactType": contactType,
        "extId": "splunk",
    }


def _generate_oncall_notification_rule(id: str, user_id: str, type: str, duration=None):
    data = {
        "id": id,
        "user_id": user_id,
        "type": type,
        "important": False,
    }

    if duration:
        data["duration"] = duration

    return data


def _generate_create_oncall_notification_rule_payload(
    user_id: str, type: str, duration=None
):
    data = {
        "user_id": user_id,
        "type": type,
        "important": False,
    }

    if duration:
        data["duration"] = duration

    return data


@pytest.mark.parametrize(
    "splunk_paging_policies,existing_oncall_notification_rules,expected_oncall_notification_rules",
    [
        ([], [], []),
        (
            [
                _generate_splunk_paging_policy(0, "sms", 60),
            ],
            [],
            [
                _generate_create_oncall_notification_rule_payload(
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
            ],
        ),
        (
            [
                _generate_splunk_paging_policy(0, "sms", 60),
            ],
            [
                _generate_oncall_notification_rule(
                    ONCALL_NOTIFICATION_POLICY_ID,
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
            ],
            [
                _generate_create_oncall_notification_rule_payload(
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
            ],
        ),
        (
            [
                _generate_splunk_paging_policy(0, "sms", 60),
                _generate_splunk_paging_policy(0, "sms", 60),
            ],
            [
                _generate_oncall_notification_rule(
                    ONCALL_NOTIFICATION_POLICY_ID,
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
            ],
            [
                _generate_create_oncall_notification_rule_payload(
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
                _generate_create_oncall_notification_rule_payload(
                    ONCALL_USER_ID,
                    "wait",
                    duration=3600,
                ),
                _generate_create_oncall_notification_rule_payload(
                    ONCALL_USER_ID,
                    "notify_by_sms",
                ),
            ],
        ),
    ],
)
@mock.patch("lib.splunk.resources.paging_policies.OnCallAPIClient")
def test_migrate_paging_policies(
    mock_oncall_api_client,
    splunk_paging_policies,
    existing_oncall_notification_rules,
    expected_oncall_notification_rules,
):
    migrate_paging_policies(
        {
            "pagingPolicies": splunk_paging_policies,
            "oncall_user": {
                "id": ONCALL_USER_ID,
                "notification_rules": existing_oncall_notification_rules,
            },
        }
    )

    mock_oncall_api_client.create.assert_has_calls(
        [
            mock.call("personal_notification_rules", payload)
            for payload in expected_oncall_notification_rules
        ]
    )

    mock_oncall_api_client.delete.assert_has_calls(
        [
            mock.call(f"personal_notification_rules/{oncall_notification_rule['id']}")
            for oncall_notification_rule in existing_oncall_notification_rules
        ]
    )
