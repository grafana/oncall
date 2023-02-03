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
from apps.slack.models import SlackChannel
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException

DIRECT_PAGING_TEAM_SELECT_ID = "paging_team_select"
DIRECT_PAGING_ORG_SELECT_ID = "paging_org_select"
DIRECT_PAGING_ESCALATION_SELECT_ID = "paging_escalation_select"
DIRECT_PAGING_USER_SELECT_ID = "paging_user_select"
DIRECT_PAGING_SCHEDULE_SELECT_ID = "paging_schedule_select"
DIRECT_PAGING_TITLE_INPUT_ID = "paging_title_input"
DIRECT_PAGING_MESSAGE_INPUT_ID = "paging_message_input"

DEFAULT_NO_ESCALATION_VALUE = "default_no_escalation"
DEFAULT_TEAM_VALUE = "default_team"


# selected user available actions
DEFAULT_POLICY = "default"
IMPORTANT_POLICY = "important"
REMOVE_ACTION = "remove"

ITEM_ACTIONS = (
    (DEFAULT_POLICY, "Set default notification policy"),
    (IMPORTANT_POLICY, "Set important notification policy"),
    (REMOVE_ACTION, "Remove from escalation"),
)


# helpers to manage current selected users/schedules state

SCHEDULES_DATA_KEY = "schedules"
USERS_DATA_KEY = "users"


def add_or_update_item(payload, key, item_pk, policy):
    metadata = json.loads(payload["view"]["private_metadata"])
    metadata[key][item_pk] = policy
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def remove_item(payload, key, item_pk):
    metadata = json.loads(payload["view"]["private_metadata"])
    if item_pk in metadata[key]:
        del metadata[key][item_pk]
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def reset_items(payload):
    metadata = json.loads(payload["view"]["private_metadata"])
    for key in (USERS_DATA_KEY, SCHEDULES_DATA_KEY):
        metadata[key] = {}
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def get_current_items(payload, key, qs):
    metadata = json.loads(payload["view"]["private_metadata"])
    items = []
    for u, p in metadata[key].items():
        item = qs.filter(pk=u).first()
        items.append((item, p))
    return items


# Slack scenario steps


class StartDirectPaging(scenario_step.ScenarioStep):
    """Handle slash command invocation and show initial dialog."""

    command_name = [settings.SLACK_DIRECT_PAGING_SLASH_COMMAND]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        input_id_prefix = _generate_input_id_prefix()

        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        private_metadata = {
            "channel_id": channel_id,
            "input_id_prefix": input_id_prefix,
            "submit_routing_uid": FinishDirectPaging.routing_uid(),
            USERS_DATA_KEY: {},
            SCHEDULES_DATA_KEY: {},
        }
        initial_payload = {"view": {"private_metadata": json.dumps(private_metadata)}}
        view = render_dialog(slack_user_identity, slack_team_identity, initial_payload, initial=True)
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class FinishDirectPaging(scenario_step.ScenarioStep):
    """Handle page command dialog submit."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        title = _get_title_from_payload(payload)
        message = _get_message_from_payload(payload)
        private_metadata = json.loads(payload["view"]["private_metadata"])
        channel_id = private_metadata["channel_id"]
        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = _get_selected_org_from_payload(payload, input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        selected_escalation = _get_selected_escalation_from_payload(payload, input_id_prefix)
        user = slack_user_identity.get_user(selected_organization)

        selected_users = [
            (u, p == IMPORTANT_POLICY)
            for u, p in get_current_items(payload, USERS_DATA_KEY, selected_organization.users)
        ]
        selected_schedules = [
            (s, p == IMPORTANT_POLICY)
            for s, p in get_current_items(payload, SCHEDULES_DATA_KEY, selected_organization.oncall_schedules)
        ]

        # trigger direct paging to selected users/schedules/escalation
        direct_paging(
            selected_organization,
            selected_team,
            user,
            title,
            message,
            selected_users,
            selected_schedules,
            selected_escalation,
        )

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


class OnPagingOrgChange(scenario_step.ScenarioStep):
    """Reload form with updated organization."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        updated_payload = reset_items(payload)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=updated_payload["trigger_id"],
            view=view,
            view_id=updated_payload["view"]["id"],
        )


class OnPagingTeamChange(OnPagingOrgChange):
    """Reload form with updated team."""


class OnPagingEscalationChange(scenario_step.ScenarioStep):
    """Set escalation chain."""


class OnPagingUserChange(scenario_step.ScenarioStep):
    """Add selected to user to the list.

    It will perform a user availability check, pushing a new modal for additional confirmation if needed.
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
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
            updated_payload = add_or_update_item(payload, USERS_DATA_KEY, selected_user.pk, DEFAULT_POLICY)
            view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
            self._slack_client.api_call(
                "views.update",
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class OnPagingItemActionChange(scenario_step.ScenarioStep):
    """Reload form with updated user details."""

    def _parse_action(self, payload):
        value = payload["actions"][0]["selected_option"]["value"]
        return value.split("|")

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, policy=None):
        policy, key, user_pk = self._parse_action(payload)

        if policy == REMOVE_ACTION:
            updated_payload = remove_item(payload, key, user_pk)
        else:
            updated_payload = add_or_update_item(payload, key, user_pk, policy)

        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnPagingConfirmUserChange(scenario_step.ScenarioStep):
    """Confirm user selection despite not being available."""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        metadata = json.loads(payload["view"]["private_metadata"])

        # recreate original view state and metadata
        private_metadata = {
            "channel_id": metadata["channel_id"],
            "input_id_prefix": metadata["input_id_prefix"],
            "submit_routing_uid": metadata["submit_routing_uid"],
            USERS_DATA_KEY: metadata[USERS_DATA_KEY],
            SCHEDULES_DATA_KEY: metadata[SCHEDULES_DATA_KEY],
        }
        previous_view_payload = {
            "view": {
                "state": metadata["state"],
                "private_metadata": json.dumps(private_metadata),
            },
        }
        # add selected user
        selected_user = _get_selected_user_from_payload(previous_view_payload, private_metadata["input_id_prefix"])
        updated_payload = add_or_update_item(previous_view_payload, USERS_DATA_KEY, selected_user.pk, DEFAULT_POLICY)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["previous_view_id"],
        )


class OnPagingScheduleChange(scenario_step.ScenarioStep):
    """Add selected to user to the list.

    It will perform a user availability check, pushing a new modal for additional confirmation if needed.
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        private_metadata = json.loads(payload["view"]["private_metadata"])
        selected_schedule = _get_selected_schedule_from_payload(payload, private_metadata["input_id_prefix"])
        if selected_schedule is None:
            return

        updated_payload = add_or_update_item(payload, SCHEDULES_DATA_KEY, selected_schedule.pk, DEFAULT_POLICY)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


# slack view/blocks rendering helpers

DIVIDER_BLOCK = {"type": "divider"}


def render_dialog(slack_user_identity, slack_team_identity, payload, initial=False):
    private_metadata = json.loads(payload["view"]["private_metadata"])
    submit_routing_uid = private_metadata.get("submit_routing_uid")
    if initial:
        # setup initial form
        new_input_id_prefix = _generate_input_id_prefix()
        new_private_metadata = private_metadata
        new_private_metadata["input_id_prefix"] = new_input_id_prefix
        selected_organization = (
            slack_team_identity.organizations.filter(users__slack_user_identity=slack_user_identity)
            .order_by("pk")
            .distinct()
            .first()
        )
        selected_team = None
        selected_escalation = None
    else:
        # setup form using data/state
        old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
            private_metadata
        )
        selected_organization = _get_selected_org_from_payload(payload, old_input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, old_input_id_prefix)
        selected_escalation = _get_selected_escalation_from_payload(payload, old_input_id_prefix)

    # widgets
    organization_select = _get_organization_select(
        slack_team_identity, slack_user_identity, selected_organization, new_input_id_prefix
    )
    team_select = _get_team_select(slack_user_identity, selected_organization, selected_team, new_input_id_prefix)
    escalation_select = _get_escalation_select(
        selected_organization, selected_team, selected_escalation, new_input_id_prefix
    )
    users_select = _get_users_select(selected_organization, selected_team, new_input_id_prefix)
    schedules_select = _get_schedules_select(selected_organization, selected_team, new_input_id_prefix)

    # blocks
    blocks = [organization_select, team_select, escalation_select, users_select, schedules_select]

    # selected items
    selected_users = get_current_items(payload, USERS_DATA_KEY, selected_organization.users)
    selected_schedules = get_current_items(payload, SCHEDULES_DATA_KEY, selected_organization.oncall_schedules)

    if selected_users or selected_schedules:
        blocks += [DIVIDER_BLOCK]
        blocks.extend(_get_selected_entries_list(new_input_id_prefix, USERS_DATA_KEY, selected_users))
        blocks.extend(_get_selected_entries_list(new_input_id_prefix, SCHEDULES_DATA_KEY, selected_schedules))
        blocks += [DIVIDER_BLOCK]

    blocks.extend([_get_title_input(payload), _get_message_input(payload)])

    view = _get_form_view(submit_routing_uid, blocks, json.dumps(new_private_metadata), selected_organization)
    return view


def _get_form_view(routing_uid, blocks, private_metatada, organization):
    try:
        channel = organization.slack_team_identity.get_cached_channels().get(
            slack_id=organization.general_log_channel_id
        )
        additional_info = f":information_source: The alert group will be posted to the #{channel.name} Slack channel"
    except SlackChannel.DoesNotExist:
        additional_info = (
            ":information_source: The alert group will be posted to the default Slack channel if there is one setup"
        )

    blocks += [
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": additional_info}],
        }
    ]
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
            "action_id": OnPagingOrgChange.routing_uid(),
            "initial_option": organizations_options[initial_option_idx],
        },
    }

    return organization_select


def _get_select_field_value(payload, prefix_id, routing_uid, field_id):
    field = payload["view"]["state"]["values"][prefix_id + field_id][routing_uid]["selected_option"]
    if field:
        return field["value"]


def _get_selected_org_from_payload(payload, input_id_prefix):
    Organization = apps.get_model("user_management", "Organization")
    selected_org_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingOrgChange.routing_uid(), DIRECT_PAGING_ORG_SELECT_ID
    )
    if selected_org_id is not None:
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
            "action_id": OnPagingTeamChange.routing_uid(),
            "initial_option": team_options[initial_option_idx],
        },
    }
    return team_select


def _get_escalation_select(organization, team, value, input_id_prefix):
    escalations = organization.escalation_chains.filter(team=team)
    # adding a default no-escalation option
    initial_option_idx = 0
    options = [
        {
            "text": {
                "type": "plain_text",
                "text": f"None",
                "emoji": True,
            },
            "value": DEFAULT_NO_ESCALATION_VALUE,
        }
    ]
    for idx, escalation in enumerate(escalations, start=1):
        if escalation == value:
            initial_option_idx = idx
        options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": f"{escalation.name}",
                    "emoji": True,
                },
                "value": f"{escalation.pk}",
            }
        )

    if not options:
        escalations_select = {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "No escalation chains available"}],
        }
    else:
        escalations_select = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Set escalation chain"},
            "block_id": input_id_prefix + DIRECT_PAGING_ESCALATION_SELECT_ID,
            "accessory": {
                "type": "static_select",
                "placeholder": {"type": "plain_text", "text": "Select an escalation", "emoji": True},
                "options": options,
                "action_id": OnPagingEscalationChange.routing_uid(),
                "initial_option": options[initial_option_idx],
            },
        }
    return escalations_select


def _get_users_select(organization, team, input_id_prefix):
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

    if not user_options:
        return {"type": "context", "elements": [{"type": "mrkdwn", "text": "No users available"}]}

    user_select = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Add responders"},
        "block_id": input_id_prefix + DIRECT_PAGING_USER_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select a user", "emoji": True},
            "action_id": OnPagingUserChange.routing_uid(),
        },
    }

    if len(user_options) > scenario_step.MAX_STATIC_SELECT_OPTIONS:
        # paginate user options in groups
        max_length = scenario_step.MAX_STATIC_SELECT_OPTIONS
        chunks = [user_options[x : x + max_length] for x in range(0, len(user_options), max_length)]
        option_groups = [
            {
                "label": {"type": "plain_text", "text": f"({(i * max_length)+1}-{(i * max_length)+max_length})"},
                "options": group,
            }
            for i, group in enumerate(chunks)
        ]
        user_select["accessory"]["option_groups"] = option_groups

    else:
        user_select["accessory"]["options"] = user_options

    return user_select


def _get_schedules_select(organization, team, input_id_prefix):
    schedules = organization.oncall_schedules.filter(team=team)

    schedule_options = [
        {
            "text": {
                "type": "plain_text",
                "text": f"{schedule.name}",
                "emoji": True,
            },
            "value": f"{schedule.pk}",
        }
        for schedule in schedules
    ]
    if not schedule_options:
        schedule_select = {"type": "context", "elements": [{"type": "mrkdwn", "text": "No schedules available"}]}
    else:
        schedule_select = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Add schedules"},
            "block_id": input_id_prefix + DIRECT_PAGING_SCHEDULE_SELECT_ID,
            "accessory": {
                "type": "static_select",
                "placeholder": {"type": "plain_text", "text": "Select a schedule", "emoji": True},
                "options": schedule_options,
                "action_id": OnPagingScheduleChange.routing_uid(),
            },
        }
    return schedule_select


def _get_selected_entries_list(input_id_prefix, key, entries):
    current_entries = []
    for entry, policy in entries:
        if key == USERS_DATA_KEY:
            icon = ":bust_in_silhouette:"
            name = entry.name or entry.username
            extra = entry.timezone
        else:
            # schedule
            icon = ":spiral_calendar_pad:"
            name = entry.name
            extra = None
        current_entries.append(
            {
                "type": "section",
                "block_id": input_id_prefix + f"{key}_{entry.pk}",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{icon} *{name}* | {policy} notifications" + (f"\n_({extra})_" if extra else ""),
                },
                "accessory": {
                    "type": "overflow",
                    "options": [
                        {"text": {"type": "plain_text", "text": f"{label}"}, "value": f"{action}|{key}|{entry.pk}"}
                        for (action, label) in ITEM_ACTIONS
                    ],
                    "action_id": OnPagingItemActionChange.routing_uid(),
                },
            }
        )
    return current_entries


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
        "callback_id": OnPagingConfirmUserChange.routing_uid(),
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
                USERS_DATA_KEY: metadata[USERS_DATA_KEY],
                SCHEDULES_DATA_KEY: metadata[SCHEDULES_DATA_KEY],
            }
        ),
    }


def _get_selected_team_from_payload(payload, input_id_prefix):
    Team = apps.get_model("user_management", "Team")
    selected_team_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingTeamChange.routing_uid(), DIRECT_PAGING_TEAM_SELECT_ID
    )
    if selected_team_id is None or selected_team_id == DEFAULT_TEAM_VALUE:
        return None
    team = Team.objects.filter(pk=selected_team_id).first()
    return team


def _get_selected_escalation_from_payload(payload, input_id_prefix):
    EscalationChain = apps.get_model("alerts", "EscalationChain")
    selected_escalation_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingEscalationChange.routing_uid(), DIRECT_PAGING_ESCALATION_SELECT_ID
    )
    if selected_escalation_id is None or selected_escalation_id == DEFAULT_NO_ESCALATION_VALUE:
        return None
    escalation = EscalationChain.objects.filter(pk=selected_escalation_id).first()
    return escalation


def _get_selected_user_from_payload(payload, input_id_prefix):
    User = apps.get_model("user_management", "User")
    selected_user_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingUserChange.routing_uid(), DIRECT_PAGING_USER_SELECT_ID
    )
    if selected_user_id is not None:
        user = User.objects.filter(pk=selected_user_id).first()
        return user


def _get_selected_schedule_from_payload(payload, input_id_prefix):
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")
    selected_schedule_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingScheduleChange.routing_uid(), DIRECT_PAGING_SCHEDULE_SELECT_ID
    )
    if selected_schedule_id is not None:
        schedule = OnCallSchedule.objects.filter(pk=selected_schedule_id).first()
        return schedule


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
        "block_action_id": OnPagingOrgChange.routing_uid(),
        "step": OnPagingOrgChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnPagingTeamChange.routing_uid(),
        "step": OnPagingTeamChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnPagingEscalationChange.routing_uid(),
        "step": OnPagingEscalationChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnPagingUserChange.routing_uid(),
        "step": OnPagingUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": OnPagingConfirmUserChange.routing_uid(),
        "step": OnPagingConfirmUserChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": OnPagingScheduleChange.routing_uid(),
        "step": OnPagingScheduleChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_OVERFLOW,
        "block_action_id": OnPagingItemActionChange.routing_uid(),
        "step": OnPagingItemActionChange,
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
