import json
from uuid import uuid4

from django.apps import apps
from django.conf import settings

from apps.alerts.paging import (
    USER_HAS_NO_NOTIFICATION_POLICY,
    USER_IS_NOT_ON_CALL,
    check_user_availability,
    direct_paging,
)
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException

DIRECT_PAGING_TEAM_SELECT_ID = "paging_team_select"
DIRECT_PAGING_ORG_SELECT_ID = "paging_org_select"
DIRECT_PAGING_ROUTE_SELECT_ID = "paging_route_select"
DIRECT_PAGING_USER_SELECT_ID = "paging_user_select"
DIRECT_PAGING_TITLE_INPUT_ID = "paging_title_input"
DIRECT_PAGING_MESSAGE_INPUT_ID = "paging_message_input"

DEFAULT_TEAM_VALUE = "default_team"


# selected user available actions
DEFAULT_POLICY = "default"
IMPORTANT_POLICY = "important"
REMOVE_ACTION = "remove"

USER_ACTIONS = (
    (DEFAULT_POLICY, "Set default notification policy"),
    (IMPORTANT_POLICY, "Set important notification policy"),
    (REMOVE_ACTION, "Remove from escalation"),
)


# helpers to manage current selected users state


def add_or_update_user(payload, user_pk, policy):
    metadata = json.loads(payload["view"]["private_metadata"])
    metadata["current_users"][user_pk] = policy
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def remove_user(payload, user_pk):
    metadata = json.loads(payload["view"]["private_metadata"])
    if user_pk in metadata["current_users"]:
        del metadata["current_users"][user_pk]
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def reset_users(payload):
    metadata = json.loads(payload["view"]["private_metadata"])
    metadata["current_users"] = {}
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def get_current_users(payload, organization):
    metadata = json.loads(payload["view"]["private_metadata"])
    current_users = []
    for u, p in metadata["current_users"].items():
        user = organization.users.filter(pk=u).first()
        current_users.append((user, p))
    return current_users


# Slack scenario steps


class StartDirectPaging(scenario_step.ScenarioStep):
    """Handle slash command invocation and show initial dialog."""

    command_name = [settings.SLACK_DIRECT_PAGING_SLASH_COMMAND]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        input_id_prefix = _generate_input_id_prefix()

        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        private_metadata = {
            "channel_id": channel_id,
            "input_id_prefix": input_id_prefix,
            "submit_routing_uid": FinishDirectPaging.routing_uid(),
            "current_users": {},
        }

        blocks = _get_initial_form_fields(slack_team_identity, slack_user_identity, input_id_prefix, payload)
        view = _get_form_view(FinishDirectPaging.routing_uid(), blocks, json.dumps(private_metadata))
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class FinishDirectPaging(scenario_step.ScenarioStep):
    """Handle page command dialog submit."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        title = _get_title_from_payload(payload)
        message = _get_message_from_payload(payload)
        private_metadata = json.loads(payload["view"]["private_metadata"])
        channel_id = private_metadata["channel_id"]
        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = _get_selected_org_from_payload(payload, input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        user = slack_user_identity.get_user(selected_organization)
        selected_users = [(u, p == IMPORTANT_POLICY) for u, p in get_current_users(payload, selected_organization)]

        # trigger direct paging to selected users
        direct_paging(selected_organization, selected_team, user, title, message, selected_users)

        try:
            self._slack_client.api_call(
                "chat.postEphemeral",
                channel=channel_id,
                user=slack_user_identity.slack_id,
                text=":white_check_mark: Alert *{}* successfully submitted".format(title),
            )
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":
                self._slack_client.api_call(
                    "chat.postEphemeral",
                    channel=slack_user_identity.im_channel_id,
                    user=slack_user_identity.slack_id,
                    text=":white_check_mark: Alert *{}* successfully submitted".format(title),
                )
            else:
                raise e


# OnChange steps, responsible for rerendering form on changed values


class OnOrgChange(scenario_step.ScenarioStep):
    """Reload form with updated organization."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        updated_payload = reset_users(payload)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnTeamChange(OnOrgChange):
    """Reload form with updated team."""


class OnUserChange(scenario_step.ScenarioStep):
    """Add selected to user to the list.

    It will perform a user availability check, pushing a new modal for additional confirmation if needed.
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        private_metadata = json.loads(payload["view"]["private_metadata"])
        selected_organization = _get_selected_org_from_payload(payload, private_metadata["input_id_prefix"])
        selected_team = _get_selected_team_from_payload(payload, private_metadata["input_id_prefix"])
        selected_user = _get_selected_user_from_payload(payload, private_metadata["input_id_prefix"])
        if selected_user is None:
            return

        # check availability
        availability_warnings = check_user_availability(selected_user, selected_team)
        if availability_warnings:
            # display warnings and require additional confirmation
            view = _display_availability_warnings(payload, availability_warnings, selected_organization, selected_user)
            self._slack_client.api_call(
                "views.push",
                trigger_id=payload["trigger_id"],
                view=view,
            )
        else:
            # user is available to be paged
            updated_payload = add_or_update_user(payload, selected_user.pk, DEFAULT_POLICY)
            view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
            self._slack_client.api_call(
                "views.update",
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class OnUserActionChange(scenario_step.ScenarioStep):
    """Reload form with updated user details."""

    def _parse_action(self, payload):
        value = payload["actions"][0]["selected_option"]["value"]
        return value.split("|")

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, policy=None):
        policy, user_pk = self._parse_action(payload)

        if policy == REMOVE_ACTION:
            updated_payload = remove_user(payload, user_pk)
        else:
            updated_payload = add_or_update_user(payload, user_pk, policy)

        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnConfirmUserChange(scenario_step.ScenarioStep):
    """Confirm user selection despite not being available."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        metadata = json.loads(payload["view"]["private_metadata"])

        # recreate original view state and metadata
        private_metadata = {
            "channel_id": metadata["channel_id"],
            "input_id_prefix": metadata["input_id_prefix"],
            "submit_routing_uid": metadata["submit_routing_uid"],
            "current_users": metadata["current_users"],
        }
        previous_view_payload = {
            "view": {
                "state": metadata["state"],
                "private_metadata": json.dumps(private_metadata),
            },
        }
        # add selected user
        selected_user = _get_selected_user_from_payload(previous_view_payload, private_metadata["input_id_prefix"])
        updated_payload = add_or_update_user(previous_view_payload, selected_user.pk, DEFAULT_POLICY)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["previous_view_id"],
        )


# slack view/blocks rendering helpers


def render_dialog(slack_user_identity, slack_team_identity, payload):
    # data/state
    private_metadata = json.loads(payload["view"]["private_metadata"])
    submit_routing_uid = private_metadata.get("submit_routing_uid")
    old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
        private_metadata
    )
    selected_organization = _get_selected_org_from_payload(payload, old_input_id_prefix)
    selected_team = _get_selected_team_from_payload(payload, old_input_id_prefix)
    selected_user = _get_selected_user_from_payload(payload, old_input_id_prefix)

    # widgets
    organization_select = _get_organization_select(
        slack_team_identity, slack_user_identity, selected_organization, new_input_id_prefix
    )
    team_select = _get_team_select(slack_user_identity, selected_organization, selected_team, new_input_id_prefix)
    users_select = _get_users_select(
        slack_user_identity, selected_organization, selected_team, selected_user, new_input_id_prefix
    )

    # blocks
    blocks = [organization_select, team_select, users_select]
    selected_users = get_current_users(payload, selected_organization)
    blocks.extend(_get_selected_users_list(new_input_id_prefix, selected_users))
    blocks.extend([_get_title_input(payload), _get_message_input(payload)])

    view = _get_form_view(submit_routing_uid, blocks, json.dumps(new_private_metadata))
    return view


def _get_form_view(routing_uid, blocks, private_metatada):
    view = {
        "type": "modal",
        "callback_id": routing_uid,
        "title": {
            "type": "plain_text",
            "text": "Create alert group",
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True,
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
        },
        "blocks": blocks,
        "private_metadata": private_metatada,
    }

    return view


def _get_initial_form_fields(slack_team_identity, slack_user_identity, input_id_prefix, payload):
    initial_organization = (
        slack_team_identity.organizations.filter(users__slack_user_identity=slack_user_identity)
        .order_by("pk")
        .distinct()
        .first()
    )

    organization_select = _get_organization_select(
        slack_team_identity, slack_user_identity, initial_organization, input_id_prefix
    )

    initial_team = None  # means default team
    initial_user = None  # no user
    team_select = _get_team_select(slack_user_identity, initial_organization, initial_team, input_id_prefix)
    users_select = _get_users_select(
        slack_user_identity, initial_organization, initial_team, initial_user, input_id_prefix
    )

    blocks = [organization_select, team_select, users_select]
    title_input = _get_title_input(payload)
    message_input = _get_message_input(payload)
    blocks.append(title_input)
    blocks.append(message_input)
    return blocks


def _get_organization_select(slack_team_identity, slack_user_identity, value, input_id_prefix):
    organizations = slack_team_identity.organizations.filter(
        users__slack_user_identity=slack_user_identity,
    ).distinct()
    organizations_options = []
    initial_option_idx = 0
    for idx, org in enumerate(organizations):
        if org == value:
            initial_option_idx = idx
        organizations_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": f"{org.stack_slug}",
                    "emoji": True,
                },
                "value": f"{org.pk}",
            }
        )

    organization_select = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Select an organization"},
        "block_id": input_id_prefix + DIRECT_PAGING_ORG_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select an organization", "emoji": True},
            "options": organizations_options,
            "action_id": OnOrgChange.routing_uid(),
            "initial_option": organizations_options[initial_option_idx],
        },
    }

    return organization_select


def _get_selected_org_from_payload(payload, input_id_prefix):
    Organization = apps.get_model("user_management", "Organization")
    selected_org_id = payload["view"]["state"]["values"][input_id_prefix + DIRECT_PAGING_ORG_SELECT_ID][
        OnOrgChange.routing_uid()
    ]["selected_option"]["value"]
    org = Organization.objects.filter(pk=selected_org_id).first()
    return org


def _get_team_select(slack_user_identity, organization, value, input_id_prefix):
    teams = organization.teams.filter(
        users__slack_user_identity=slack_user_identity,
    ).distinct()

    team_options = []
    # Adding pseudo option for default team
    initial_option_idx = 0
    team_options.append(
        {
            "text": {
                "type": "plain_text",
                "text": f"General",
                "emoji": True,
            },
            "value": DEFAULT_TEAM_VALUE,
        }
    )
    for idx, team in enumerate(teams, start=1):
        if team == value:
            initial_option_idx = idx
        team_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": f"{team.name}",
                    "emoji": True,
                },
                "value": f"{team.pk}",
            }
        )

    team_select = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Select a team"},
        "block_id": input_id_prefix + DIRECT_PAGING_TEAM_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select a team", "emoji": True},
            "options": team_options,
            "action_id": OnTeamChange.routing_uid(),
            "initial_option": team_options[initial_option_idx],
        },
    }
    return team_select


def _get_users_select(slack_user_identity, organization, team, value, input_id_prefix):
    users = organization.users.all()
    if team is not None:
        users = users.filter(teams=team)

    user_options = [
        {
            "text": {
                "type": "plain_text",
                "text": f"{user.name or user.username}",
                "emoji": True,
            },
            "value": f"{user.pk}",
        }
        for user in users
    ]

    user_select = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Add responders"},
        "block_id": input_id_prefix + DIRECT_PAGING_USER_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select a user", "emoji": True},
            "options": user_options,
            "action_id": OnUserChange.routing_uid(),
        },
    }
    return user_select


def _get_selected_users_list(input_id_prefix, users):
    user_entries = (
        [{"type": "divider"}]
        + [
            {
                "type": "section",
                "block_id": input_id_prefix + f"user_{u.pk}",
                "text": {"type": "mrkdwn", "text": f"*{u.name or u.username}* | {p} notifications\n_({u.timezone})_"},
                "accessory": {
                    "type": "overflow",
                    "options": [
                        {"text": {"type": "plain_text", "text": f"{label}"}, "value": f"{action}|{u.pk}"}
                        for (action, label) in USER_ACTIONS
                    ],
                    "action_id": OnUserActionChange.routing_uid(),
                },
            }
            for u, p in users
        ]
        + [{"type": "divider"}]
    )
    return user_entries


def _display_availability_warnings(payload, warnings, organization, user):
    metadata = json.loads(payload["view"]["private_metadata"])

    messages = []
    for w in warnings:
        if w["error"] == USER_IS_NOT_ON_CALL:
            messages.append(
                f":warning: User *{user.name or user.username}* is not on-call.\nWe recommend you to select on-call users first."
            )
            schedules_available = w["data"].get("schedules", {})
            if schedules_available:
                messages.append(":information_source: Currently on-call from schedules:")
            for schedule, users in schedules_available.items():
                oncall_users = organization.users.filter(public_primary_key__in=users)
                usernames = ", ".join(f"*{u.name or u.username}*" for u in oncall_users)
                messages.append(f":spiral_calendar_pad: {schedule}: {usernames}")
        elif w["error"] == USER_HAS_NO_NOTIFICATION_POLICY:
            messages.append(f":warning: User *{user.name or user.username}* has no notification policy setup.")

    return {
        "type": "modal",
        "callback_id": OnConfirmUserChange.routing_uid(),
        "title": {"type": "plain_text", "text": "Are you sure?"},
        "submit": {"type": "plain_text", "text": "Confirm"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            }
            for message in messages
        ],
        "private_metadata": json.dumps(
            {
                "state": payload["view"]["state"],
                "input_id_prefix": metadata["input_id_prefix"],
                "channel_id": metadata["channel_id"],
                "submit_routing_uid": metadata["submit_routing_uid"],
                "current_users": metadata["current_users"],
            }
        ),
    }


def _get_selected_team_from_payload(payload, input_id_prefix):
    Team = apps.get_model("user_management", "Team")
    selected_team_id = payload["view"]["state"]["values"][input_id_prefix + DIRECT_PAGING_TEAM_SELECT_ID][
        OnTeamChange.routing_uid()
    ]["selected_option"]["value"]
    if selected_team_id == DEFAULT_TEAM_VALUE:
        return None
    team = Team.objects.filter(pk=selected_team_id).first()
    return team


def _get_selected_user_from_payload(payload, input_id_prefix):
    User = apps.get_model("user_management", "User")
    selected_option = payload["view"]["state"]["values"][input_id_prefix + DIRECT_PAGING_USER_SELECT_ID][
        OnUserChange.routing_uid()
    ]["selected_option"]
    if selected_option is not None:
        selected_user_id = selected_option["value"]
        user = User.objects.filter(pk=selected_user_id).first()
        return user


def _get_and_change_input_id_prefix_from_metadata(metadata):
    old_input_id_prefix = metadata["input_id_prefix"]
    new_input_id_prefix = _generate_input_id_prefix()
    metadata["input_id_prefix"] = new_input_id_prefix
    return old_input_id_prefix, new_input_id_prefix, metadata


def _get_title_input(payload):
    title_input_block = {
        "type": "input",
        "block_id": DIRECT_PAGING_TITLE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Title:",
        },
        "element": {
            "type": "plain_text_input",
            "action_id": FinishDirectPaging.routing_uid(),
            "placeholder": {
                "type": "plain_text",
                "text": " ",
            },
        },
    }
    if payload.get("text", None) is not None:
        title_input_block["element"]["initial_value"] = payload["text"]
    return title_input_block


def _get_title_from_payload(payload):
    title = payload["view"]["state"]["values"][DIRECT_PAGING_TITLE_INPUT_ID][FinishDirectPaging.routing_uid()]["value"]
    return title


def _get_message_input(payload):
    message_input_block = {
        "type": "input",
        "block_id": DIRECT_PAGING_MESSAGE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Message:",
        },
        "element": {
            "type": "plain_text_input",
            "action_id": FinishDirectPaging.routing_uid(),
            "multiline": True,
            "placeholder": {
                "type": "plain_text",
                "text": " ",
            },
        },
        "optional": True,
    }
    if payload.get("message", {}).get("text") is not None:
        message_input_block["element"]["initial_value"] = payload["message"]["text"]
    return message_input_block


def _get_message_from_payload(payload):
    message = (
        payload["view"]["state"]["values"][DIRECT_PAGING_MESSAGE_INPUT_ID][FinishDirectPaging.routing_uid()]["value"]
        or ""
    )
    return message


# _generate_input_id_prefix returns uniq str to not to preserve input's values between view update
#  https://api.slack.com/methods/views.update#markdown
def _generate_input_id_prefix():
    return str(uuid4())


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnOrgChange.routing_uid(),
        "step": OnOrgChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnTeamChange.routing_uid(),
        "step": OnTeamChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnUserChange.routing_uid(),
        "step": OnUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": OnConfirmUserChange.routing_uid(),
        "step": OnConfirmUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_OVERFLOW,
        "block_action_id": OnUserActionChange.routing_uid(),
        "step": OnUserActionChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_SLASH_COMMAND,
        "command_name": StartDirectPaging.command_name,
        "step": StartDirectPaging,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": FinishDirectPaging.routing_uid(),
        "step": FinishDirectPaging,
    },
]
