from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_TO_ONCALL_CONTACT_METHOD_MAP,
    PRESERVE_EXISTING_USER_NOTIFICATION_RULES,
)


def migrate_notification_rules(user: dict) -> None:
    """Migrate user notification rules from OpsGenie to Grafana OnCall."""
    if (
        PRESERVE_EXISTING_USER_NOTIFICATION_RULES
        and user["oncall_user"]["notification_rules"]
    ):
        return

    # Delete existing notification rules if any
    for rule in user["oncall_user"]["notification_rules"]:
        OnCallAPIClient.delete(f"personal_notification_rules/{rule['id']}")

    # Create new notification rules
    for rule in user["notification_rules"]:
        if rule["enabled"]:
            oncall_type = OPSGENIE_TO_ONCALL_CONTACT_METHOD_MAP.get(rule["type"])
            if oncall_type:
                payload = {
                    "user_id": user["oncall_user"]["id"],
                    "type": oncall_type,
                    "important": rule.get("criteria", {}).get("isHighPriority", False),
                }
                if rule.get("delay"):
                    # Convert delay from minutes to seconds
                    payload["duration"] = rule["delay"] * 60
                OnCallAPIClient.create("personal_notification_rules", payload)
