from lib.common.report import ERROR_SIGN, SUCCESS_SIGN, TAB, WARNING_SIGN
from lib.opsgenie.config import (
    PRESERVE_EXISTING_USER_NOTIFICATION_RULES,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
)


def format_user(user: dict) -> str:
    """Format user for display in reports."""
    return f"{user['fullName']} ({user['username']})"


def format_schedule(schedule: dict) -> str:
    """Format schedule for display in reports."""
    return schedule["name"]


def format_escalation_policy(policy: dict) -> str:
    """Format escalation policy for display in reports."""
    return policy["name"]


def format_integration(integration: dict) -> str:
    """Format integration for display in reports."""
    return f"{integration['name']} ({integration['type']})"


def user_report(users: list[dict]) -> str:
    """Generate report for user migration status."""
    report = ["User notification rules report:"]
    for user in users:
        if user.get("oncall_user"):
            if (
                user["oncall_user"]["notification_rules"]
                and PRESERVE_EXISTING_USER_NOTIFICATION_RULES
            ):
                report.append(
                    f"{TAB}{WARNING_SIGN} {format_user(user)} (existing notification rules will be preserved "
                    "because PRESERVE_EXISTING_USER_NOTIFICATION_RULES is true)"
                )
            elif (
                user["oncall_user"]["notification_rules"]
                and not PRESERVE_EXISTING_USER_NOTIFICATION_RULES
            ):
                report.append(
                    f"{TAB}{WARNING_SIGN} {format_user(user)} (existing notification rules will be deleted "
                    "because PRESERVE_EXISTING_USER_NOTIFICATION_RULES is false)"
                )
            else:
                report.append(f"{TAB}{SUCCESS_SIGN} {format_user(user)}")
        else:
            report.append(
                f"{TAB}{ERROR_SIGN} {format_user(user)} — no Grafana OnCall user found with this email"
            )
    return "\n".join(report)


def schedule_report(schedules: list[dict]) -> str:
    """Generate report for schedule migration status."""
    report = ["Schedule report:"]
    for schedule in schedules:
        if schedule.get("migration_errors"):
            errors = schedule["migration_errors"]
            report.append(f"{TAB}{ERROR_SIGN} {format_schedule(schedule)} —")
            for error in errors:
                report.append(f"{TAB}{TAB}- {error}")
        elif schedule.get("oncall_schedule"):
            report.append(
                f"{TAB}{WARNING_SIGN} {format_schedule(schedule)} (existing schedule will be deleted)"
            )
        else:
            report.append(f"{TAB}{SUCCESS_SIGN} {format_schedule(schedule)}")
    return "\n".join(report)


def escalation_policy_report(policies: list[dict]) -> str:
    """Generate report for escalation policy migration status."""
    report = ["Escalation policy report:"]
    for policy in policies:
        if policy.get("oncall_escalation_chain"):
            report.append(
                f"{TAB}{WARNING_SIGN} {format_escalation_policy(policy)} (existing escalation chain will be deleted)"
            )
        else:
            report.append(f"{TAB}{SUCCESS_SIGN} {format_escalation_policy(policy)}")
    return "\n".join(report)


def integration_report(integrations: list[dict]) -> str:
    """Generate report for integration migration status."""
    report = ["Integration report:"]
    for integration in integrations:
        if integration.get("oncall_integration"):
            report.append(
                f"{TAB}{WARNING_SIGN} {format_integration(integration)} (existing integration will be deleted)"
            )
        elif (
            not integration.get("oncall_type")
            and not UNSUPPORTED_INTEGRATION_TO_WEBHOOKS
        ):
            report.append(
                f"{TAB}{ERROR_SIGN} {format_integration(integration)} — unsupported integration type"
            )
        elif not integration.get("oncall_type") and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
            report.append(
                f"{TAB}{WARNING_SIGN} {format_integration(integration)} — unsupported integration type, will be migrated as webhook"
            )
        else:
            report.append(f"{TAB}{SUCCESS_SIGN} {format_integration(integration)}")
    return "\n".join(report)
