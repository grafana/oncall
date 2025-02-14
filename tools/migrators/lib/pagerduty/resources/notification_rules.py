import copy

from lib.oncall.api_client import OnCallAPIClient
from lib.pagerduty.config import (
    PAGERDUTY_TO_ONCALL_CONTACT_METHOD_MAP,
    PRESERVE_EXISTING_USER_NOTIFICATION_RULES,
)
from lib.utils import remove_duplicates, transform_wait_delay


def remove_duplicate_rules_between_waits(rules: list[dict]) -> list[dict]:
    """
    Remove duplicate rules in chunks between wait rules.
    E.g. "SMS - SMS - 1min - Phone call" becomes "SMS - 1min - Phone call"
    """
    rules_copy = copy.deepcopy(rules)

    for method in set(PAGERDUTY_TO_ONCALL_CONTACT_METHOD_MAP.values()):
        rules_copy = remove_duplicates(
            rules_copy,
            split_condition=lambda rule: rule["type"] == "wait",
            duplicate_condition=lambda rule: rule["type"] == method,
        )

    return rules_copy


def migrate_notification_rules(user: dict) -> None:
    if (
        PRESERVE_EXISTING_USER_NOTIFICATION_RULES
        and user["oncall_user"]["notification_rules"]
    ):
        print(f"Preserving existing notification rules for {user['email']}")
        return

    notification_rules = [
        rule for rule in user["notification_rules"] if rule["urgency"] == "high"
    ]

    for important in (False, True):
        oncall_rules = transform_notification_rules(
            notification_rules, user["oncall_user"]["id"], important
        )

        for rule in oncall_rules:
            OnCallAPIClient.create("personal_notification_rules", rule)

        if oncall_rules:
            # delete old notification rules if any new rules were created
            for rule in user["oncall_user"]["notification_rules"]:
                if rule["important"] == important:
                    OnCallAPIClient.delete(
                        "personal_notification_rules/{}".format(rule["id"])
                    )


def transform_notification_rules(
    notification_rules: list[dict], user_id: str, important: bool
) -> list[dict]:
    """
    Transform PagerDuty user notification rules to Grafana OnCall personal notification rules.
    """
    notification_rules = sorted(
        notification_rules, key=lambda rule: rule["start_delay_in_minutes"]
    )

    oncall_notification_rules = []
    for idx, rule in enumerate(notification_rules):
        delay = rule["start_delay_in_minutes"]

        if idx > 0:
            previous_delay = notification_rules[idx - 1]["start_delay_in_minutes"]
            delay -= previous_delay

        oncall_notification_rules += transform_notification_rule(
            rule, delay, user_id, important
        )

    oncall_notification_rules = remove_duplicate_rules_between_waits(
        oncall_notification_rules
    )

    return oncall_notification_rules


def transform_notification_rule(
    notification_rule: dict, delay: int, user_id: str, important: bool
) -> list[dict]:
    contact_method_type = notification_rule["contact_method"]["type"]
    oncall_type = PAGERDUTY_TO_ONCALL_CONTACT_METHOD_MAP[contact_method_type]

    notify_rule = {"user_id": user_id, "type": oncall_type, "important": important}

    if not delay:
        return [notify_rule]

    wait_rule = {
        "user_id": user_id,
        "type": "wait",
        "duration": transform_wait_delay(delay),
        "important": important,
    }
    return [wait_rule, notify_rule]
