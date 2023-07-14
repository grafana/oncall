from django.apps import apps
from django.db.models import OuterRef, Subquery
from django.utils.text import slugify

from apps.alerts.models import EscalationPolicy
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal


class TerraformFileRenderer:
    AMIXR_USER_DATA_TEMPLATE = '\ndata "amixr_user" "{}" {{\n    username = "{}"\n}}\n'

    TEAM_DATA_TEMPLATE = '\ndata "amixr_team" "{}" {{\n    name = "{}"\n}}\n'

    CUSTOM_ACTION_DATA_TEMPLATE = (
        '\ndata "amixr_action" "{}" {{\n    name = "{}"\n    integration_id = amixr_integration.{}.id\n}}\n'
    )

    SCHEDULE_DATA_TEMPLATE = '\ndata "amixr_schedule" "{}" {{\n    name = "{}"\n}}\n'

    USER_GROUP_DATA_TEMPLATE = '\ndata "amixr_user_group" "{}" {{\n    slack_handle = "{}"\n}}\n'

    SLACK_CHANNEL_DATA_TEMPLATE = '\ndata "amixr_slack_channel" "{}" {{\n    name = "{}"\n}}\n'

    INTEGRATION_RESOURCE_TEMPLATE = (
        '\nresource "amixr_integration" "{}" {{\n    name = "{}"\n    type = "{}"\n    team_id = {}\n}}\n'
    )
    INTEGRATION_RESOURCE_TEMPLATE_WITH_TEMPLATES = (
        '\nresource "amixr_integration" "{}" {{\n'
        '    name      = "{}"\n'
        '    type      = "{}"\n'
        "    team_id   = {}\n"
        "    templates {}\n"
        "}}\n"
    )
    ROUTE_RESOURCES_TEMPLATE = (
        '\nresource "amixr_route" "{}" {{\n'
        "    integration_id = amixr_integration.{}.id\n"
        "    escalation_chain_id = {}.id\n"
        '    routing_regex = "{}"\n'
        "    position = {}\n"
        "}}\n"
    )
    ROUTE_RESOURCES_TEMPLATE_WITH_SLACK = (
        '\nresource "amixr_route" "{}" {{\n'
        "    integration_id = amixr_integration.{}.id\n"
        "    escalation_chain_id = {}.id\n"
        '    routing_regex = "{}"\n'
        "    position = {}\n"
        "    slack {{\n"
        "        channel_id = {}\n"
        "    }}\n"
        "}}\n"
    )

    ESCALATION_CHAIN_DATA_TEMPLATE = '\ndata "amixr_escalation_chain" "{}" {{\n    name = "{}"\n}}\n'

    ESCALATION_CHAIN_RESOURCE_TEMPLATE = (
        '\nresource "amixr_escalation_chain" "{}" {{\n    name = "{}"\n    team_id = {}\n}}\n'
    )

    ESCALATION_POLICY_TEMPLATES = {
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[EscalationPolicy.STEP_WAIT]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    duration = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    important = {}\n"
        "    persons_to_notify = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    persons_to_notify_next_each_time = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_SCHEDULE
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    important = {}\n"
        "    notify_on_call_from_schedule = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_GROUP
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    important = {}\n"
        "    group_to_notify = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    action_to_trigger = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_IF_TIME
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    notify_if_time_from = {}\n"
        "    notify_if_time_to = {}\n"
        "    position = {}\n"
        "}}\n",
        EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[
            EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW
        ]: '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    num_alerts_in_window = {}\n"
        "    num_minutes_in_window = {}\n"
        "    position = {}\n"
        "}}\n",
        "step_is_none": '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        "    type = null\n"
        "    position = {}\n"
        "}}\n",
        "other_steps": '\nresource "amixr_escalation" "{}" {{\n'
        "    escalation_chain_id = {}\n"
        '    type = "{}"\n'
        "    position = {}\n"
        "}}\n",
    }

    AMIXR_USERS_LIST_TEMPLATE = "[\n        {}\n    ]"
    AMIXR_USERS_LIST_TEMPLATE_EMPTY = "[]"
    ROLLING_USERS_TEMPLATE = "        [{}],\n"
    ROLLING_USERS_LIST_TEMPLATE = "[\n{}    ]"

    SCHEDULE_RESOURCE_TEMPLATE_ICAL = (
        '\nresource "amixr_schedule" "{}" {{\n'
        '    name = "{}"\n'
        '    type = "ical"\n'
        "    team_id = {}\n"
        "    ical_url_primary = {}\n"
        "    ical_url_overrides = {}\n"
        "{}"
        "}}\n"
    )

    SCHEDULE_RESOURCE_TEMPLATE_CALENDAR = (
        '\nresource "amixr_schedule" "{}" {{\n'
        '    name = "{}"\n'
        '    type = "calendar"\n'
        "    team_id = {}\n"
        '    time_zone = "{}"\n'
        "{}"
        "}}\n"
    )

    SCHEDULE_RESOURCE_SLACK_TEMPLATE = "    slack {{\n        channel_id = {}\n    }}\n"

    ON_CALL_SHIFT_RESOURCE_TEMPLATE_RECURRENT_EVENT = (
        '\nresource "amixr_on_call_shift" "{}" {{\n'
        '    name = "{}"\n'
        '    type = "{}"\n'
        "    team_id = {}\n"
        '    start = "{}"\n'
        "    duration = {}\n"
        "    level = {}\n"
        '    frequency = "{}"\n'
        "    interval = {}\n"
        '    week_start = "{}"\n'
        "    by_day = {}\n"
        "    by_month = {}\n"
        "    by_monthday = {}\n"
        "    users = {}\n"
        "}}\n"
    )

    ON_CALL_SHIFT_RESOURCE_TEMPLATE_ROLLING_USERS = (
        '\nresource "amixr_on_call_shift" "{}" {{\n'
        '    name = "{}"\n'
        '    type = "{}"\n'
        "    team_id = {}\n"
        '    start = "{}"\n'
        "    duration = {}\n"
        "    level = {}\n"
        '    frequency = "{}"\n'
        "    interval = {}\n"
        '    week_start = "{}"\n'
        "    by_day = {}\n"
        "    by_month = {}\n"
        "    by_monthday = {}\n"
        "    rolling_users = {}\n"
        "}}\n"
    )

    ON_CALL_SHIFT_RESOURCE_TEMPLATE_SINGLE_EVENT = (
        '\nresource "amixr_on_call_shift" "{}" {{\n'
        '    name = "{}"\n'
        '    type = "{}"\n'
        "    team_id = {}\n"
        '    start = "{}"\n'
        "    duration = {}\n"
        "    level = {}\n"
        "    users = {}\n"
        "}}\n"
    )

    def __init__(self, organization):
        self.organization = organization
        self.data = {}
        self.used_names = {}

    def render_terraform_file(self):
        result = self.render_resource_text()
        data_result = self.render_data_text()
        result = data_result + result
        if len(result) == 0:
            result += "There is nothing here yet. Check Settings to add integration and come back!"
        return result

    def render_resource_text(self):
        result = ""

        result += self.render_escalation_chains_related_resources_text()

        integrations_related_resources_text = self.render_integrations_related_resources_text()
        result += integrations_related_resources_text

        shifts_related_resources_text = self.render_on_call_shift_resource_text()
        result += shifts_related_resources_text

        schedules_related_resources_text = self.render_schedules_related_resources_text()
        result += schedules_related_resources_text

        return result

    def render_escalation_chains_related_resources_text(self):
        result = ""
        escalation_chains = self.organization.escalation_chains.all()

        for escalation_chain in escalation_chains:
            resource_name = self.escape_string_for_terraform(escalation_chain.name)
            team_name = self.render_team_name(escalation_chain.team)
            team_name_text = f"data.amixr_team.{team_name}.id" if team_name else "null"
            result += self.ESCALATION_CHAIN_RESOURCE_TEMPLATE.format(
                resource_name, escalation_chain.name, team_name_text
            )
            result += self.render_escalation_policy_resource_text(escalation_chain, resource_name)

        return result

    def render_escalation_policy_resource_text(self, escalation_chain, escalation_chain_resource_name):
        result = ""
        escalation_policies = escalation_chain.escalation_policies.all()

        escalation_chain_id = f"amixr_escalation_chain.{escalation_chain_resource_name}.id"

        for num, escalation_policy in enumerate(escalation_policies, start=1):
            escalation_name = f"escalation-{num}-{escalation_chain_resource_name}"
            step_type = None

            if escalation_policy.step is None:
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES["step_is_none"].format(
                    escalation_name,
                    escalation_chain_id,
                    escalation_policy.order,
                )
            else:
                step_type = EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[escalation_policy.step]

            if escalation_policy.step == EscalationPolicy.STEP_WAIT:
                wait_delay = escalation_policy.wait_delay
                delay = int(wait_delay.total_seconds()) if wait_delay is not None else "null"
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    delay,
                    escalation_policy.order,
                )
            elif escalation_policy.step in [
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
                EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
                EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
            ]:
                persons_to_notify = escalation_policy.sorted_users_queue
                important = escalation_policy.step == EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT
                important = "true" if important else "false"
                rendered_persons_to_notify = self.render_amixr_users_list_text(persons_to_notify)

                if escalation_policy.step == EscalationPolicy.STEP_NOTIFY_USERS_QUEUE:
                    result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                        escalation_name,
                        escalation_chain_id,
                        step_type,
                        rendered_persons_to_notify,
                        escalation_policy.order,
                    )
                else:
                    result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                        escalation_name,
                        escalation_chain_id,
                        step_type,
                        important,
                        rendered_persons_to_notify,
                        escalation_policy.order,
                    )
            elif escalation_policy.step in [
                EscalationPolicy.STEP_NOTIFY_SCHEDULE,
                EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
            ]:
                schedule = escalation_policy.notify_schedule
                schedule_name = self.render_name(schedule, "schedules", "name")
                schedule_text = "null"
                if schedule is not None:
                    schedule_text = f"amixr_schedule.{schedule_name}.id"

                important = escalation_policy.step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT
                important = "true" if important else "false"

                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    important,
                    schedule_text,
                    escalation_policy.order,
                )
            elif escalation_policy.step in [
                EscalationPolicy.STEP_NOTIFY_GROUP,
                EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
            ]:
                user_group = escalation_policy.notify_to_group
                user_group_name = self.render_user_group_name(user_group)
                important = escalation_policy.step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT
                important = "true" if important else "false"
                user_group_text = f"data.amixr_user_group.{user_group_name}.id" if user_group else "null"
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    important,
                    user_group_text,
                    escalation_policy.order,
                )
            # TODO: uncomment after custom actions refactoring
            # elif escalation_policy.step == EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
            #     custom_action = escalation_policy.custom_button_trigger
            #     custom_action_name = self.render_name(custom_action, "custom_actions", "name")
            #     self.render_custom_action_data_source(custom_action, custom_action_name, integration_resource_name)
            #     custom_action_text = f"data.amixr_action.{custom_action_name}.id" if custom_action else "null"
            #     result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
            #         escalation_name, escalation_chain_id, step_type, custom_action_text, escalation_policy.order,
            #     )
            elif escalation_policy.step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
                from_time = self.render_time_string(escalation_policy.from_time)
                to_time = self.render_time_string(escalation_policy.to_time)
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    from_time,
                    to_time,
                    escalation_policy.order,
                )
            elif escalation_policy.step == EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES[step_type].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    escalation_policy.num_alerts_in_window,
                    escalation_policy.num_minutes_in_window,
                    escalation_policy.order,
                )
            elif escalation_policy.step is not None:
                result += TerraformFileRenderer.ESCALATION_POLICY_TEMPLATES["other_steps"].format(
                    escalation_name,
                    escalation_chain_id,
                    step_type,
                    escalation_policy.order,
                )
        return result

    def render_integrations_related_resources_text(self):
        result = ""
        integrations = self.organization.alert_receive_channels.all().order_by("created_at")
        for integration in integrations:
            integration_resource_name = self.render_name(integration, "integrations", "verbal_name")
            team_name = self.render_team_name(integration.team)
            team_name_text = f"data.amixr_team.{team_name}.id" if team_name else "null"
            formatted_integration_name = self.escape_string_for_terraform(integration.verbal_name)
            templates = self.render_integration_template(integration)
            if templates is not None:
                result += TerraformFileRenderer.INTEGRATION_RESOURCE_TEMPLATE_WITH_TEMPLATES.format(
                    integration_resource_name,
                    formatted_integration_name,
                    integration.integration,
                    team_name_text,
                    templates,
                )
            else:
                result += TerraformFileRenderer.INTEGRATION_RESOURCE_TEMPLATE.format(
                    integration_resource_name,
                    formatted_integration_name,
                    integration.integration,
                    team_name_text,
                )
            route_text = self.render_route_resource_text(integration, integration_resource_name)
            # render data sources for custom actions just after integration resource
            actions_data_text = self.render_action_data_text()
            result += actions_data_text

            result += route_text
        return result

    def render_route_resource_text(self, integration, integration_resource_name):
        SlackChannel = apps.get_model("slack", "SlackChannel")
        slack_team_identity = self.organization.slack_team_identity
        slack_channels_q = SlackChannel.objects.filter(
            slack_id=OuterRef("slack_channel_id"),
            slack_team_identity=slack_team_identity,
        )
        routes = integration.channel_filters.all().annotate(
            slack_channel_name=Subquery(slack_channels_q.values("name")[:1])
        )
        result = ""
        for num, route in enumerate(routes, start=1):
            if route.is_default:
                continue
            route_name = f"route-{num}-{integration_resource_name}"

            escalation_chain_resource_name = "amixr_escalation_chain." + self.escape_string_for_terraform(
                route.escalation_chain.name
            )

            routing_regex = self.escape_string_for_terraform(route.filtering_term)
            if route.slack_channel_id is not None:
                if route.slack_channel_name is not None:
                    slack_channel_data_name = f"slack-channel-{route.slack_channel_name}"
                    slack_channel_id = f"data.amixr_slack_channel.{slack_channel_data_name}.slack_id"
                    if route.slack_channel_name not in self.data.setdefault("slack_channels", {}):
                        data_result = TerraformFileRenderer.SLACK_CHANNEL_DATA_TEMPLATE.format(
                            slack_channel_data_name,
                            route.slack_channel_name,
                        )
                        self.data["slack_channels"][route.slack_channel_name] = data_result
                else:
                    slack_channel_id = f'"{route.slack_channel_id}"'
                result += TerraformFileRenderer.ROUTE_RESOURCES_TEMPLATE_WITH_SLACK.format(
                    route_name,
                    integration_resource_name,
                    escalation_chain_resource_name,
                    routing_regex,
                    route.order,
                    slack_channel_id,
                )
            else:
                result += TerraformFileRenderer.ROUTE_RESOURCES_TEMPLATE.format(
                    route_name,
                    integration_resource_name,
                    escalation_chain_resource_name,
                    routing_regex,
                    route.order,
                )

        return result

    def render_schedules_related_resources_text(self):
        SlackChannel = apps.get_model("slack", "SlackChannel")
        slack_team_identity = self.organization.slack_team_identity
        slack_channels_q = SlackChannel.objects.filter(
            slack_id=OuterRef("channel"),
            slack_team_identity=slack_team_identity,
        )
        schedules = self.organization.oncall_schedules.annotate(
            slack_channel_name=Subquery(slack_channels_q.values("name")[:1])
        ).order_by("pk")
        result = ""
        for schedule in schedules:
            schedule_name = self.render_name(schedule, "schedules", "name")
            formatted_schedule_name = self.escape_string_for_terraform(schedule.name)
            team_name = self.render_team_name(schedule.team)
            team_name_text = f"data.amixr_team.{team_name}.id" if team_name else "null"
            slack_channel_text = ""
            if schedule.channel is not None:
                if schedule.slack_channel_name is not None:
                    slack_channel_data_name = f"slack-channel-{schedule.slack_channel_name}"
                    slack_channel_id = f"data.amixr_slack_channel.{slack_channel_data_name}.slack_id"
                    if schedule.slack_channel_name not in self.data.setdefault("slack_channels", {}):
                        data_result = TerraformFileRenderer.SLACK_CHANNEL_DATA_TEMPLATE.format(
                            slack_channel_data_name,
                            schedule.slack_channel_name,
                        )
                        self.data["slack_channels"][schedule.slack_channel_name] = data_result
                else:
                    slack_channel_id = f'"{schedule.channel}"'

                slack_channel_text = TerraformFileRenderer.SCHEDULE_RESOURCE_SLACK_TEMPLATE.format(slack_channel_id)

            if isinstance(schedule, OnCallScheduleICal):
                ical_url_primary = f'"{schedule.ical_url_primary}"' if schedule.ical_url_primary else "null"
                ical_url_overrides = f'"{schedule.ical_url_overrides}"' if schedule.ical_url_overrides else "null"
                result += TerraformFileRenderer.SCHEDULE_RESOURCE_TEMPLATE_ICAL.format(
                    schedule_name,
                    formatted_schedule_name,
                    team_name_text,
                    ical_url_primary,
                    ical_url_overrides,
                    slack_channel_text,
                )

            elif isinstance(schedule, OnCallScheduleCalendar):
                result += TerraformFileRenderer.SCHEDULE_RESOURCE_TEMPLATE_CALENDAR.format(
                    schedule_name, formatted_schedule_name, team_name_text, schedule.time_zone, slack_channel_text
                )
        return result

    def render_on_call_shift_resource_text(self):
        CustomOnCallShift = apps.get_model("schedules", "CustomOnCallShift")
        result = ""
        on_call_shifts = self.organization.custom_on_call_shifts.all().order_by("pk")

        for shift in on_call_shifts:
            shift_name = self.render_name(shift, "on_call_shifts", "name")
            team_name = self.render_team_name(shift.team)
            team_name_text = f"data.amixr_team.{team_name}.id" if team_name else "null"
            formatted_integration_name = self.escape_string_for_terraform(shift.name)
            shift_type = CustomOnCallShift.PUBLIC_TYPE_CHOICES_MAP[shift.type]
            start = shift.start.strftime("%Y-%m-%dT%H:%M:%S")
            duration = int(shift.duration.total_seconds())
            level = shift.priority_level
            frequency = CustomOnCallShift.PUBLIC_FREQUENCY_CHOICES_MAP.get(shift.frequency)
            interval = shift.interval or "null"
            week_start = CustomOnCallShift.ICAL_WEEKDAY_MAP[shift.week_start]
            by_day = self.replace_quotes(f"{shift.by_day}") if shift.by_day else "null"
            by_month = self.replace_quotes(f"{shift.by_day}") if shift.by_month else "null"
            by_monthday = self.replace_quotes(f"{shift.by_day}") if shift.by_monthday else "null"

            if shift.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
                rolling_amixr_users = shift.get_rolling_users()
                rendered_amixr_users = self.render_rolling_users_list_text(rolling_amixr_users)
                result += TerraformFileRenderer.ON_CALL_SHIFT_RESOURCE_TEMPLATE_ROLLING_USERS.format(
                    shift_name,
                    formatted_integration_name,
                    shift_type,
                    team_name_text,
                    start,
                    duration,
                    level,
                    frequency,
                    interval,
                    week_start,
                    by_day,
                    by_month,
                    by_monthday,
                    rendered_amixr_users,
                )
            else:
                amixr_users = shift.users.all()
                rendered_amixr_users = self.render_amixr_users_list_text(amixr_users)

                if shift.type == CustomOnCallShift.TYPE_SINGLE_EVENT:
                    result += TerraformFileRenderer.ON_CALL_SHIFT_RESOURCE_TEMPLATE_SINGLE_EVENT.format(
                        shift_name,
                        formatted_integration_name,
                        shift_type,
                        team_name_text,
                        start,
                        duration,
                        level,
                        rendered_amixr_users,
                    )
                elif shift.type == CustomOnCallShift.TYPE_RECURRENT_EVENT:
                    result += TerraformFileRenderer.ON_CALL_SHIFT_RESOURCE_TEMPLATE_RECURRENT_EVENT.format(
                        shift_name,
                        formatted_integration_name,
                        shift_type,
                        team_name_text,
                        start,
                        duration,
                        level,
                        frequency,
                        interval,
                        week_start,
                        by_day,
                        by_month,
                        by_monthday,
                        rendered_amixr_users,
                    )
        return result

    def render_data_text(self):
        result = ""
        for data_type, data_source in sorted(self.data.items(), key=lambda x: x[0], reverse=True):
            for data_result in data_source:
                result += data_source[data_result]
        return result

    def render_action_data_text(self):
        result = ""
        actions = self.data.pop("custom_actions", {})
        for action, action_text in actions.items():
            result += action_text
        return result

    def render_names_and_data_for_amixr_users(self, amixr_users):
        amixr_users_names = []
        for user in amixr_users:
            user_data_name = self.render_name(user, "users", "username")
            amixr_users_names.append(user_data_name)
            if user.public_primary_key not in self.data.setdefault("users", {}):
                data_result = TerraformFileRenderer.AMIXR_USER_DATA_TEMPLATE.format(user_data_name, user.username)
                self.data["users"][user.public_primary_key] = data_result
        return amixr_users_names

    def render_rolling_users_list_text(self, rolling_amixr_users):
        if rolling_amixr_users:
            rolling_users_text = ""
            for amixr_users in rolling_amixr_users:
                if amixr_users:
                    amixr_users_names = self.render_names_and_data_for_amixr_users(amixr_users)
                    rendered_amixr_users = ", ".join(
                        [f"data.amixr_user.{user_verbal}.id" for user_verbal in amixr_users_names]
                    )
                else:
                    rendered_amixr_users = TerraformFileRenderer.AMIXR_USERS_LIST_TEMPLATE_EMPTY
                rolling_users_text += TerraformFileRenderer.ROLLING_USERS_TEMPLATE.format(rendered_amixr_users)
            rendered_rolling_users = TerraformFileRenderer.ROLLING_USERS_LIST_TEMPLATE.format(rolling_users_text)
        else:
            rendered_rolling_users = TerraformFileRenderer.AMIXR_USERS_LIST_TEMPLATE_EMPTY
        return rendered_rolling_users

    def render_amixr_users_list_text(self, amixr_users):
        if amixr_users:
            amixr_users_names = self.render_names_and_data_for_amixr_users(amixr_users)
            rendered_amixr_users = TerraformFileRenderer.AMIXR_USERS_LIST_TEMPLATE.format(
                ", ".join([f"data.amixr_user.{user_verbal}.id" for user_verbal in amixr_users_names])
            )
        else:
            rendered_amixr_users = TerraformFileRenderer.AMIXR_USERS_LIST_TEMPLATE_EMPTY
        return rendered_amixr_users

    def render_name(self, obj, obj_verbal, name_attr):
        if obj is None:
            return None
        obj_name = slugify(getattr(obj, name_attr))
        obj_data_name = obj_name
        counter = 1
        while (
            obj_data_name in self.used_names.setdefault(obj_verbal, {})
            and self.used_names[obj_verbal][obj_data_name] != obj.pk
        ):
            counter += 1
            obj_data_name = f"{obj_name}-{counter}"
        self.used_names[obj_verbal][obj_data_name] = obj.pk
        return obj_data_name

    def render_schedule_data_source(self, schedule, schedule_data_name):
        if schedule is None:
            return None
        if schedule.pk not in self.data.setdefault("schedules", {}):
            formatted_schedule_name = self.escape_string_for_terraform(schedule.name)
            data_result = TerraformFileRenderer.SCHEDULE_DATA_TEMPLATE.format(
                schedule_data_name, formatted_schedule_name
            )
            self.data["schedules"][schedule.pk] = data_result

    def render_user_group_name(self, user_group):
        if user_group is None:
            return None
        user_group_data_name = slugify(user_group.handle)
        if user_group.pk not in self.data.setdefault("user_groups", {}):
            data_result = TerraformFileRenderer.USER_GROUP_DATA_TEMPLATE.format(user_group_data_name, user_group.handle)
            self.data["user_groups"][user_group.pk] = data_result
        return user_group_data_name

    def render_team_name(self, team):
        if team is None:
            return None

        team_data_name = slugify(team.name)
        if team.pk not in self.data.setdefault("teams", {}):
            data_result = TerraformFileRenderer.TEAM_DATA_TEMPLATE.format(team_data_name, team.name)
            self.data["teams"][team.pk] = data_result
        return team_data_name

    def render_custom_action_data_source(self, custom_action, custom_action_data_name, integration_resource_name):
        if custom_action is None:
            return None
        if custom_action.pk not in self.data.setdefault("custom_actions", {}):
            formatted_action_name = self.escape_string_for_terraform(custom_action.name)
            data_result = TerraformFileRenderer.CUSTOM_ACTION_DATA_TEMPLATE.format(
                custom_action_data_name,
                formatted_action_name,
                integration_resource_name,
            )
            self.data["custom_actions"][custom_action.pk] = data_result

    def render_integration_template(self, integration):
        result_template = None
        slack_template = self.render_integration_slack_template(integration)
        template_fields = {
            "resolve_signal": integration.resolve_condition_template,
            "grouping_key": integration.grouping_id_template,
        }

        templates = {}
        for template_type, template in template_fields.items():
            if template is not None:
                if "\n" in template:
                    result = ""
                    template_lines = template.split("\n")
                    for line in template_lines:
                        result += f"                {line}\n"
                    result = "<<-EOT\n" "{}" "        EOT".format(result)
                    templates[template_type] = result
                else:
                    template = self.escape_string_for_terraform(template)
                    templates[template_type] = f'"{template}"'

        if len(templates) > 0 or slack_template:
            result_template = "{\n"
            for template_type, template in templates.items():
                result_template += f"        {template_type} = {template}\n"
            if slack_template:
                result_template += f"        slack {slack_template}"
            result_template += "    }"

        return result_template

    def render_integration_slack_template(self, integration):
        slack_template = None
        slack_fields = {
            "title": integration.slack_title_template,
            "message": integration.slack_message_template,
            "image_url": integration.slack_image_url_template,
        }
        slack_templates = {}
        for template_type, template in slack_fields.items():
            if template is not None:
                if "\n" in template:
                    result = ""
                    template_lines = template.split("\n")
                    for line in template_lines:
                        result += f"                {line}\n"
                    result = "<<-EOT\n" "{}" "            EOT".format(result)
                    slack_templates[template_type] = result
                else:
                    template = self.escape_string_for_terraform(template)
                    slack_templates[template_type] = f'"{template}"'

        if len(slack_templates) > 0:
            slack_template = "{\n"
            for template_type, template in slack_templates.items():
                slack_template += f"            {template_type} = {template}\n"
            slack_template += "        }\n"

        return slack_template

    def render_time_string(self, time_obj):
        result = f"\"{time_obj.strftime('%H:%M:%SZ')}\"" if time_obj is not None else "null"
        return result

    def escape_string_for_terraform(self, template_line):
        template_line = template_line.replace("\\", "\\\\")
        template_line = template_line.replace('"', r"\"")
        return template_line

    def replace_quotes(self, template_line):
        template_line = template_line.replace("'", r'"')
        return template_line
