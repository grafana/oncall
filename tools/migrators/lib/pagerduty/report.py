from typing import Any, List

from lib.common.report import ERROR_SIGN, SUCCESS_SIGN, TAB, WARNING_SIGN
from lib.pagerduty.config import PRESERVE_EXISTING_USER_NOTIFICATION_RULES


def format_user(user: dict) -> str:
    result = "{} ({})".format(user["name"], user["email"])

    if user["oncall_user"]:
        result = "{} {}".format(SUCCESS_SIGN, result)
    else:
        result = "{} {} — no Grafana OnCall user found with this email".format(
            ERROR_SIGN, result
        )

    return result


def format_schedule(schedule: dict) -> str:
    if schedule["unmatched_users"] and schedule["migration_errors"]:
        result = "{} {} — schedule references unmatched users and some layers cannot be migrated".format(
            ERROR_SIGN, schedule["name"]
        )
    elif schedule["unmatched_users"]:
        result = "{} {} — schedule references unmatched users".format(
            ERROR_SIGN, schedule["name"]
        )
    elif schedule["migration_errors"]:
        result = "{} {} — some layers cannot be migrated".format(
            ERROR_SIGN, schedule["name"]
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, schedule["name"])

    return result


def format_escalation_policy(policy: dict) -> str:
    if policy["unmatched_users"] and policy["flawed_schedules"]:
        result = "{} {} — policy references unmatched users and schedules that cannot be migrated".format(
            ERROR_SIGN, policy["name"]
        )
    elif policy["unmatched_users"]:
        result = "{} {} — policy references unmatched users".format(
            ERROR_SIGN, policy["name"]
        )
    elif policy["flawed_schedules"]:
        result = "{} {} — policy references schedules that cannot be migrated".format(
            ERROR_SIGN, policy["name"]
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, policy["name"])

    return result


def format_integration(integration: dict) -> str:
    result = "{} - {}".format(integration["service"]["name"], integration["name"])

    if not integration["oncall_type"]:
        result = (
            "{} {} — cannot find appropriate Grafana OnCall integration type".format(
                ERROR_SIGN, result
            )
        )

        if integration["vendor_name"]:
            result += ": '{}'".format(integration["vendor_name"])

    elif integration["is_escalation_policy_flawed"]:
        policy_name = integration["service"]["escalation_policy"]["summary"]
        result = "{} {} — escalation policy '{}' references unmatched users or schedules that cannot be migrated".format(
            ERROR_SIGN, result, policy_name
        )
    else:
        # check if integration not supported, but UNSUPPORTED_INTEGRATION_TO_WEBHOOKS set
        if integration.get("converted_to_webhook", False):
            result = "{} {} – cannot find appropriate Grafana OnCall integration type, integration will be migrated with type 'webhook'".format(
                WARNING_SIGN, result
            )
        else:
            result = "{} {}".format(SUCCESS_SIGN, result)

    return result


def user_report(users: list[dict]) -> str:
    result = "User notification rules report:"

    for user in sorted(users, key=lambda u: bool(u["oncall_user"]), reverse=True):
        result += "\n" + TAB + format_user(user)

        if user["oncall_user"]:
            if (
                user["oncall_user"]["notification_rules"]
                and PRESERVE_EXISTING_USER_NOTIFICATION_RULES
            ):
                # already has user notification rules defined in OnCall.. we won't touch these
                result += " (existing notification rules will be preserved due to the PRESERVE_EXISTING_USER_NOTIFICATION_RULES being set to True and this user already having notification rules defined in OnCall)"
            elif (
                user["oncall_user"]["notification_rules"]
                and not PRESERVE_EXISTING_USER_NOTIFICATION_RULES
            ):
                # already has user notification rules defined in OnCall.. we will overwrite these
                result += " (existing notification rules will be overwritten due to the PRESERVE_EXISTING_USER_NOTIFICATION_RULES being set to False)"
            elif user["notification_rules"]:
                # user has notification rules defined in PagerDuty, but none defined in OnCall, we will migrate these
                result += " (existing PagerDuty notification rules will be migrated due to this user not having any notification rules defined in OnCall)"

    return result


def schedule_report(schedules: list[dict]) -> str:
    result = "Schedule report:"

    for schedule in sorted(
        schedules, key=lambda s: bool(s["unmatched_users"] or s["migration_errors"])
    ):
        result += "\n" + TAB + format_schedule(schedule)

        if (
            not schedule["unmatched_users"]
            and schedule["oncall_schedule"]
            and not schedule["migration_errors"]
        ):
            result += " (existing schedule with name '{}' will be deleted)".format(
                schedule["oncall_schedule"]["name"]
            )

        for user in schedule["unmatched_users"]:
            result += "\n" + TAB * 2 + format_user(user)

        for error in schedule["migration_errors"]:
            result += "\n" + TAB * 2 + "{} {}".format(ERROR_SIGN, error)

    return result


def escalation_policy_report(policies: list[dict]) -> str:
    result = "Escalation policy report: "

    for policy in sorted(
        policies, key=lambda p: bool(p["unmatched_users"] or p["flawed_schedules"])
    ):
        result += "\n" + TAB + format_escalation_policy(policy)

        for user in policy["unmatched_users"]:
            result += "\n" + TAB * 2 + format_user(user)

        for schedule in policy["flawed_schedules"]:
            result += "\n" + TAB * 2 + format_schedule(schedule)

        if (
            not policy["unmatched_users"]
            and not policy["flawed_schedules"]
            and policy["oncall_escalation_chain"]
        ):
            result += (
                " (existing escalation chain with name '{}' will be deleted)".format(
                    policy["oncall_escalation_chain"]["name"]
                )
            )

    return result


def integration_report(integrations: list[dict]) -> str:
    result = "Integration report:"

    for integration in sorted(
        integrations,
        key=lambda i: bool(i["oncall_type"] and not i["is_escalation_policy_flawed"]),
        reverse=True,
    ):
        result += "\n" + TAB + format_integration(integration)
        if (
            integration["oncall_type"]
            and not integration["is_escalation_policy_flawed"]
            and integration["oncall_integration"]
        ):
            result += " (existing integration with name '{}' will be deleted)".format(
                integration["oncall_integration"]["name"]
            )

    return result


def format_ruleset(ruleset: dict) -> str:
    if ruleset["flawed_escalation_policies"]:
        escalation_policy_names = [
            p["name"] for p in ruleset["flawed_escalation_policies"]
        ]
        result = "{} {} — escalation policies '{}' reference unmatched users or schedules that cannot be migrated".format(
            ERROR_SIGN, ruleset["name"], ", ".join(escalation_policy_names)
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, ruleset["name"])

    return result


def ruleset_report(rulesets: list[dict]) -> str:
    result = "Event rules (global rulesets) report:"

    for ruleset in sorted(
        rulesets,
        key=lambda r: bool(r["flawed_escalation_policies"]),
        reverse=True,
    ):
        result += "\n" + TAB + format_ruleset(ruleset)
        if not ruleset["flawed_escalation_policies"] and ruleset["oncall_integration"]:
            result += " (existing integration with name '{}' will be deleted)".format(
                ruleset["oncall_name"]
            )

    return result


def format_service(service: Any, will_be_migrated: bool = True) -> str:
    """Format a service for reporting."""
    service_type = (
        "Business Service"
        if hasattr(service, "business_service")
        else "Technical Service"
    )
    result = f"{service.name} ({service_type})"

    if not will_be_migrated:
        result = f"{ERROR_SIGN} {result} — Service was filtered out"
    elif hasattr(service, "migration_errors") and service.migration_errors:
        result = f"{ERROR_SIGN} {result} — {service.migration_errors}"
    else:
        result = f"{SUCCESS_SIGN} {result}"

    return result


def services_report(
    all_technical_services: List[Any],
    all_business_services: List[Any],
    filtered_technical_services: List[Any],
    filtered_business_services: List[Any],
) -> str:
    """Generate a report of services to be migrated."""
    result = "Services migration report:"

    # Create sets of service IDs that will be migrated
    technical_ids = {s.id for s in filtered_technical_services}
    business_ids = {s.id for s in filtered_business_services}

    # Report technical services
    result += "\n" + TAB + "Technical Services:"
    for service in sorted(
        all_technical_services, key=lambda service: service.id not in technical_ids
    ):
        result += "\n" + TAB * 2 + format_service(service, service.id in technical_ids)

    # Report business services
    result += "\n" + TAB + "Business Services:"
    for service in sorted(
        all_business_services, key=lambda service: service.id not in business_ids
    ):
        result += "\n" + TAB * 2 + format_service(service, service.id in business_ids)

    return result
