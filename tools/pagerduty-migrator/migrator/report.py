TAB = " " * 4
SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"


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
    if schedule["unmatched_users"]:
        result = "{} {} — schedule references unmatched users".format(
            ERROR_SIGN, schedule["name"]
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, schedule["name"])

    return result


def format_escalation_policy(policy: dict) -> str:
    if policy["unmatched_users"] and policy["flawed_schedules"]:
        result = "{} {} — policy references unmatched users and schedules with unmatched users".format(
            ERROR_SIGN, policy["name"]
        )
    elif policy["unmatched_users"]:
        result = "{} {} — policy references unmatched users".format(
            ERROR_SIGN, policy["name"]
        )
    elif policy["flawed_schedules"]:
        result = "{} {} — policy references schedules with unmatched users".format(
            ERROR_SIGN, policy["name"]
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, policy["name"])

    return result


def format_integration(integration: dict) -> str:
    result = integration["service"]["name"] + " - " + integration["name"]

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
        result = "{} {} — escalation policy '{}' references unmatched users or schedules with unmatched users".format(
            ERROR_SIGN, result, policy_name
        )
    else:
        result = "{} {}".format(SUCCESS_SIGN, result)

    return result


def user_report(users: list[dict]) -> str:
    result = "User notification rules report:"

    for user in sorted(users, key=lambda u: bool(u["oncall_user"]), reverse=True):
        result += "\n" + TAB + format_user(user)

        if user["oncall_user"] and user["notification_rules"]:
            result += " (existing notification rules will be deleted)"

    return result


def schedule_report(schedules: list[dict]) -> str:
    result = "Schedule report:"

    for schedule in sorted(schedules, key=lambda s: bool(s["unmatched_users"])):
        result += "\n" + TAB + format_schedule(schedule)

        if not schedule["unmatched_users"] and schedule["oncall_schedule"]:
            result += " (existing schedule with name '{}' will be deleted)".format(
                schedule["oncall_schedule"]["name"]
            )

        for user in schedule["unmatched_users"]:
            result += "\n" + TAB * 2 + format_user(user)

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
