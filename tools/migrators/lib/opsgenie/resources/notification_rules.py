from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_TO_ONCALL_CONTACT_METHOD_MAP,
    PRESERVE_EXISTING_USER_NOTIFICATION_RULES,
)
from lib.utils import transform_wait_delay


def migrate_notification_rules(user: dict) -> None:
    """Migrate user notification rules from OpsGenie to Grafana OnCall."""
    if (
        PRESERVE_EXISTING_USER_NOTIFICATION_RULES
        and user["oncall_user"]["notification_rules"]
    ):
        print(
            f"Preserving existing notification rules for {user.get('email', user.get('username'))}"
        )
        return

    # If not preserving, delete ALL existing notification rules first
    if (
        not PRESERVE_EXISTING_USER_NOTIFICATION_RULES
        and user["oncall_user"]["notification_rules"]
    ):
        print(
            f"Deleting existing notification rules for {user.get('email', user.get('username'))}"
        )
        for rule in user["oncall_user"]["notification_rules"]:
            OnCallAPIClient.delete(f"personal_notification_rules/{rule['id']}")

    # Create notification rules for both important=False and important=True
    for important in (False, True):
        # Get the OnCall rules for the current importance level
        oncall_rules = transform_notification_rules(
            user["notification_rules"], user["oncall_user"]["id"], important
        )

        # Create the new rules
        for rule in oncall_rules:
            OnCallAPIClient.create("personal_notification_rules", rule)


def transform_notification_rules(
    notification_steps: list[dict], user_id: str, important: bool
) -> list[dict]:
    """
    Transform OpsGenie notification steps to OnCall personal notification rules.
    If a step has timeAmount > 0, add a wait step before the notification.
    """
    # Sort steps by sendAfter minutes (or 0 if not present)
    sorted_steps = sorted(
        notification_steps,
        key=lambda step: step.get("sendAfter", {}).get("timeAmount", 0),
    )

    oncall_rules = []

    # Process steps in order
    for step in sorted_steps:
        if not step.get("enabled", False):
            continue

        # Get the current time amount
        time_amount = step.get("sendAfter", {}).get("timeAmount", 0)

        # If time amount is not 0, add a wait rule
        if time_amount > 0:
            wait_rule = {
                "user_id": user_id,
                "type": "wait",
                "duration": transform_wait_delay(time_amount),
                "important": important,
            }
            oncall_rules.append(wait_rule)

        # Get the method type from the contact object inside the step
        contact_method = step.get("contact", {}).get("method")

        # Special handling for mobile notifications when important=True
        if contact_method == "mobile" and important:
            oncall_type = "notify_by_mobile_app_critical"
        else:
            oncall_type = OPSGENIE_TO_ONCALL_CONTACT_METHOD_MAP.get(contact_method)

        if not oncall_type:
            continue

        # Add the notification rule
        notify_rule = {"user_id": user_id, "type": oncall_type, "important": important}
        oncall_rules.append(notify_rule)

    return oncall_rules
