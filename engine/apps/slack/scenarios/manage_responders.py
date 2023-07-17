import json

from django.apps import apps

from apps.alerts.paging import check_user_availability, direct_paging, unpage_user
from apps.slack.scenarios import scenario_step
from apps.slack.scenarios.paging import (
    DIRECT_PAGING_SCHEDULE_SELECT_ID,
    DIRECT_PAGING_USER_SELECT_ID,
    _generate_input_id_prefix,
    _get_availability_warnings_view,
    _get_schedules_select,
    _get_select_field_value,
    _get_users_select,
)
from apps.slack.scenarios.step_mixins import AlertGroupActionsMixin

MANAGE_RESPONDERS_USER_SELECT_ID = "responders_user_select"
MANAGE_RESPONDERS_SCHEDULE_SELECT_ID = "responders_schedule_select"

SCHEDULE_DATA_KEY = "schedule"
USER_DATA_KEY = "user"

# Slack scenario steps


class StartManageResponders(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    """Handle slash command invocation and show initial dialog."""  # TODO

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        view = render_dialog(alert_group)
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class ManageRespondersUserChange(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        organization = alert_group.channel.organization

        # check availability
        availability_warnings = check_user_availability(selected_user)
        if availability_warnings:
            # display warnings and require additional confirmation
            view = _get_availability_warnings_view(
                availability_warnings,
                organization,
                selected_user,
                ManageRespondersConfirmUserChange.routing_uid(),
                json.dumps({USER_DATA_KEY: selected_user.id, "alert_group_pk": alert_group.pk}),
            )
            self._slack_client.api_call(
                "views.push",
                trigger_id=payload["trigger_id"],
                view=view,
            )
        else:
            direct_paging(
                organization=organization,
                team=alert_group.channel.team,
                from_user=slack_user_identity.get_user(organization),
                users=[(selected_user, False)],
                alert_group=alert_group,
            )
            view = render_dialog(alert_group)
            self._slack_client.api_call(
                "views.update",
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class ManageRespondersConfirmUserChange(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        organization = alert_group.channel.organization

        direct_paging(
            organization=organization,
            team=alert_group.channel.team,
            from_user=slack_user_identity.get_user(organization),
            users=[(selected_user, False)],
            alert_group=alert_group,
        )
        view = render_dialog(alert_group)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["previous_view_id"],
        )


class ManageRespondersScheduleChange(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = _get_alert_group_from_payload(payload)
        selected_schedule = _get_selected_schedule_from_payload(payload)
        organization = alert_group.channel.organization

        direct_paging(
            organization=organization,
            team=alert_group.channel.team,
            from_user=slack_user_identity.get_user(organization),
            schedules=[(selected_schedule, False)],
            alert_group=alert_group,
        )
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=render_dialog(alert_group),
            view_id=payload["view"]["id"],
        )


class ManageRespondersRemoveUser(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        from_user = slack_user_identity.get_user(alert_group.channel.organization)

        unpage_user(alert_group, selected_user, from_user)
        view = render_dialog(alert_group)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


# slack view/blocks rendering helpers

DIVIDER_BLOCK = {"type": "divider"}


def render_dialog(alert_group):
    blocks = []

    paged_users = alert_group.get_paged_users()
    for user in alert_group.get_paged_users():
        blocks += [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f":bust_in_silhouette: *{user.name or user.username}*"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Remove", "emoji": True},
                    "action_id": ManageRespondersRemoveUser.routing_uid(),
                    "value": str(user.pk),
                },
            }
        ]
    if paged_users:
        blocks += [DIVIDER_BLOCK]

    input_id_prefix = _generate_input_id_prefix()

    blocks += [
        _get_users_select(alert_group.channel.organization, input_id_prefix, ManageRespondersUserChange.routing_uid())
    ]
    blocks += [
        _get_schedules_select(
            alert_group.channel.organization, input_id_prefix, ManageRespondersScheduleChange.routing_uid()
        )
    ]

    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Add responders",
        },
        "blocks": blocks,
        "private_metadata": json.dumps({"alert_group_pk": alert_group.pk, "input_id_prefix": input_id_prefix}),
    }
    return view


def _get_selected_user_from_payload(payload):
    User = apps.get_model("user_management", "User")

    try:
        selected_user_id = payload["actions"][0]["value"]
    except KeyError:
        try:
            selected_user_id = json.loads(payload["view"]["private_metadata"])[USER_DATA_KEY]
        except KeyError:
            input_id_prefix = json.loads(payload["view"]["private_metadata"])["input_id_prefix"]
            selected_user_id = _get_select_field_value(
                payload, input_id_prefix, ManageRespondersUserChange.routing_uid(), DIRECT_PAGING_USER_SELECT_ID
            )

    return User.objects.get(pk=selected_user_id)


def _get_selected_schedule_from_payload(payload):
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    try:
        selected_schedule_id = json.loads(payload["view"]["private_metadata"])[SCHEDULE_DATA_KEY]
    except KeyError:
        input_id_prefix = json.loads(payload["view"]["private_metadata"])["input_id_prefix"]
        selected_schedule_id = _get_select_field_value(
            payload, input_id_prefix, ManageRespondersScheduleChange.routing_uid(), DIRECT_PAGING_SCHEDULE_SELECT_ID
        )

    return OnCallSchedule.objects.get(pk=selected_schedule_id)


def _get_alert_group_from_payload(payload):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group_pk = json.loads(payload["view"]["private_metadata"])["alert_group_pk"]
    return AlertGroup.all_objects.get(pk=alert_group_pk)


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": ManageRespondersUserChange.routing_uid(),
        "step": ManageRespondersUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": ManageRespondersConfirmUserChange.routing_uid(),
        "step": ManageRespondersConfirmUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": ManageRespondersScheduleChange.routing_uid(),
        "step": ManageRespondersScheduleChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": ManageRespondersRemoveUser.routing_uid(),
        "step": ManageRespondersRemoveUser,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": StartManageResponders.routing_uid(),
        "step": StartManageResponders,
    },
]
