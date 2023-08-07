import enum
import json
import typing
from uuid import uuid4

from django.conf import settings
from django.db.models import Model, QuerySet

from apps.alerts.models import AlertReceiveChannel, EscalationChain
from apps.alerts.paging import (
    AvailabilityWarning,
    PagingError,
    ScheduleNotifications,
    UserNotifications,
    check_user_availability,
    direct_paging,
)
from apps.slack.constants import DIVIDER, PRIVATE_METADATA_MAX_LENGTH
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException
from apps.slack.types import (
    Block,
    BlockActionType,
    CompositionObjectOption,
    CompositionObjectOptionGroup,
    EventPayload,
    ModalView,
    PayloadType,
    ScenarioRoute,
)

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.schedules.models import OnCallSchedule
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.user_management.models import Organization, Team, User


DIRECT_PAGING_TEAM_SELECT_ID = "paging_team_select"
DIRECT_PAGING_ORG_SELECT_ID = "paging_org_select"
DIRECT_PAGING_USER_SELECT_ID = "paging_user_select"
DIRECT_PAGING_SCHEDULE_SELECT_ID = "paging_schedule_select"
DIRECT_PAGING_TITLE_INPUT_ID = "paging_title_input"
DIRECT_PAGING_MESSAGE_INPUT_ID = "paging_message_input"
DIRECT_PAGING_ADDITIONAL_RESPONDERS_INPUT_ID = "paging_additional_responders_input"

DEFAULT_TEAM_VALUE = "default_team"


class Policy(enum.StrEnum):
    """
    selected user available actions
    """

    DEFAULT = "default"
    IMPORTANT = "important"
    REMOVE_ACTION = "remove"


ITEM_ACTIONS = (
    (Policy.DEFAULT, "Set default notification policy"),
    (Policy.IMPORTANT, "Set important notification policy"),
    (Policy.REMOVE_ACTION, "Remove from escalation"),
)


# helpers to manage current selected users/schedules state


class DataKey(enum.StrEnum):
    SCHEDULES = "schedules"
    USERS = "users"


# https://api.slack.com/reference/block-kit/block-elements#static_select
MAX_STATIC_SELECT_OPTIONS = 100


def add_or_update_item(payload: EventPayload, key: DataKey, item_pk: str, policy: Policy) -> EventPayload:
    metadata = json.loads(payload["view"]["private_metadata"])
    metadata[key][item_pk] = policy
    updated_metadata = json.dumps(metadata)
    if len(updated_metadata) > PRIVATE_METADATA_MAX_LENGTH:
        raise ValueError("Cannot add entry, maximum exceeded")
    payload["view"]["private_metadata"] = updated_metadata
    return payload


def remove_item(payload: EventPayload, key: DataKey, item_pk: str) -> EventPayload:
    metadata = json.loads(payload["view"]["private_metadata"])
    if item_pk in metadata[key]:
        del metadata[key][item_pk]
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


def reset_items(payload: EventPayload) -> EventPayload:
    metadata = json.loads(payload["view"]["private_metadata"])
    for key in (DataKey.USERS, DataKey.SCHEDULES):
        metadata[key] = {}
    payload["view"]["private_metadata"] = json.dumps(metadata)
    return payload


T = typing.TypeVar("T", bound=Model)


def get_current_items(
    payload: EventPayload, key: DataKey, qs: "RelatedManager['T']"
) -> typing.List[typing.Tuple[T, Policy]]:
    metadata = json.loads(payload["view"]["private_metadata"])
    items: typing.List[typing.Tuple[T, Policy]] = []
    for u, p in metadata[key].items():
        item = qs.filter(pk=u).first()
        items.append((item, p))
    return items


# Slack scenario steps


class StartDirectPaging(scenario_step.ScenarioStep):
    """Handle slash command invocation and show initial dialog."""

    command_name = [settings.SLACK_DIRECT_PAGING_SLASH_COMMAND]

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        input_id_prefix = _generate_input_id_prefix()

        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        private_metadata = {
            "channel_id": channel_id,
            "input_id_prefix": input_id_prefix,
            "submit_routing_uid": FinishDirectPaging.routing_uid(),
            DataKey.USERS: {},
            DataKey.SCHEDULES: {},
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

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        title = _get_title_from_payload(payload)
        message = _get_message_from_payload(payload)
        private_metadata = json.loads(payload["view"]["private_metadata"])
        channel_id = private_metadata["channel_id"]
        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = _get_selected_org_from_payload(
            payload, input_id_prefix, slack_team_identity, slack_user_identity
        )
        _, selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        user = slack_user_identity.get_user(selected_organization)

        # Only pass users/schedules if additional responders checkbox is checked
        selected_users: UserNotifications | None = None
        selected_schedules: ScheduleNotifications | None = None

        is_additional_responders_checked = _get_additional_responders_checked_from_payload(payload, input_id_prefix)
        if is_additional_responders_checked:
            selected_users = [
                (u, p == Policy.IMPORTANT)
                for u, p in get_current_items(payload, DataKey.USERS, selected_organization.users)
            ]
            selected_schedules = [
                (s, p == Policy.IMPORTANT)
                for s, p in get_current_items(payload, DataKey.SCHEDULES, selected_organization.oncall_schedules)
            ]

        # trigger direct paging to selected team + users/schedules
        alert_group = direct_paging(
            selected_organization,
            selected_team,
            user,
            title,
            message,
            selected_users,
            selected_schedules,
        )

        text = ":white_check_mark: Alert group *{}* created: {}".format(title, alert_group.web_link)

        try:
            self._slack_client.api_call(
                "chat.postEphemeral",
                channel=channel_id,
                user=slack_user_identity.slack_id,
                text=text,
            )
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":
                self._slack_client.api_call(
                    "chat.postEphemeral",
                    channel=slack_user_identity.im_channel_id,
                    user=slack_user_identity.slack_id,
                    text=text,
                )
            else:
                raise e


# OnChange steps, responsible for rerendering form on changed values


class OnPagingOrgChange(scenario_step.ScenarioStep):
    """Reload form with updated organization."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        updated_payload = reset_items(payload)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=updated_payload["trigger_id"],
            view=view,
            view_id=updated_payload["view"]["id"],
        )


class OnPagingTeamChange(scenario_step.ScenarioStep):
    """Set team."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        view = render_dialog(slack_user_identity, slack_team_identity, payload)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnPagingCheckAdditionalResponders(OnPagingOrgChange):
    """Check/uncheck additional responders checkbox."""


class OnPagingUserChange(scenario_step.ScenarioStep):
    """Add selected to user to the list.

    It will perform a user availability check, pushing a new modal for additional confirmation if needed.
    """

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        private_metadata = json.loads(payload["view"]["private_metadata"])
        selected_organization = _get_selected_org_from_payload(
            payload, private_metadata["input_id_prefix"], slack_team_identity, slack_user_identity
        )
        selected_user = _get_selected_user_from_payload(payload, private_metadata["input_id_prefix"])
        if selected_user is None:
            return

        # check availability
        availability_warnings = check_user_availability(selected_user)
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
            error_msg = None
            try:
                updated_payload = add_or_update_item(payload, DataKey.USERS, selected_user.pk, Policy.DEFAULT)
            except ValueError:
                updated_payload = payload
                error_msg = "Cannot add user, maximum responders exceeded"
            view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
            self._slack_client.api_call(
                "views.update",
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class OnPagingItemActionChange(scenario_step.ScenarioStep):
    """Reload form with updated user details."""

    def _parse_action(self, payload: EventPayload) -> typing.Tuple[Policy, str, str]:
        value = payload["actions"][0]["selected_option"]["value"]
        return value.split("|")

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        policy, key, user_pk = self._parse_action(payload)

        error_msg = None
        if policy == Policy.REMOVE_ACTION:
            updated_payload = remove_item(payload, key, user_pk)
        else:
            try:
                updated_payload = add_or_update_item(payload, key, user_pk, policy)
            except ValueError:
                updated_payload = payload
                error_msg = "Cannot update policy, maximum responders exceeded"

        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnPagingConfirmUserChange(scenario_step.ScenarioStep):
    """Confirm user selection despite not being available."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        metadata = json.loads(payload["view"]["private_metadata"])

        # recreate original view state and metadata
        private_metadata = {
            "channel_id": metadata["channel_id"],
            "input_id_prefix": metadata["input_id_prefix"],
            "submit_routing_uid": metadata["submit_routing_uid"],
            DataKey.USERS: metadata[DataKey.USERS],
            DataKey.SCHEDULES: metadata[DataKey.SCHEDULES],
        }
        previous_view_payload = {
            "view": {
                "state": metadata["state"],
                "private_metadata": json.dumps(private_metadata),
            },
        }
        # add selected user
        selected_user = _get_selected_user_from_payload(previous_view_payload, private_metadata["input_id_prefix"])
        error_msg = None
        try:
            updated_payload = add_or_update_item(previous_view_payload, DataKey.USERS, selected_user.pk, Policy.DEFAULT)
        except ValueError:
            updated_payload = payload
            error_msg = "Cannot add user, maximum responders exceeded"
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
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

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        private_metadata = json.loads(payload["view"]["private_metadata"])
        selected_schedule = _get_selected_schedule_from_payload(payload, private_metadata["input_id_prefix"])
        if selected_schedule is None:
            return

        error_msg = None
        try:
            updated_payload = add_or_update_item(payload, DataKey.SCHEDULES, selected_schedule.pk, Policy.DEFAULT)
        except ValueError:
            updated_payload = payload
            error_msg = "Cannot add schedule, maximum responders exceeded"
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


# slack view/blocks rendering helpers


def render_dialog(
    slack_user_identity: "SlackUserIdentity",
    slack_team_identity: "SlackTeamIdentity",
    payload: EventPayload,
    initial=False,
    error_msg=None,
) -> ModalView:
    private_metadata = json.loads(payload["view"]["private_metadata"])
    submit_routing_uid = private_metadata.get("submit_routing_uid")

    # Get organizations available to user
    available_organizations = _get_available_organizations(slack_team_identity, slack_user_identity)

    if initial:
        # setup initial form
        new_input_id_prefix = _generate_input_id_prefix()
        new_private_metadata = private_metadata
        new_private_metadata["input_id_prefix"] = new_input_id_prefix
        selected_organization = available_organizations.first()
        is_team_selected, selected_team = False, None
        is_additional_responders_checked = False
    else:
        # setup form using data/state
        old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
            private_metadata
        )
        selected_organization = _get_selected_org_from_payload(
            payload, old_input_id_prefix, slack_team_identity, slack_user_identity
        )
        is_team_selected, selected_team = _get_selected_team_from_payload(payload, old_input_id_prefix)
        is_additional_responders_checked = _get_additional_responders_checked_from_payload(payload, old_input_id_prefix)

    # widgets
    team_select_blocks = _get_team_select_blocks(
        slack_user_identity, selected_organization, is_team_selected, selected_team, new_input_id_prefix
    )
    additional_responders_blocks = _get_additional_responders_blocks(
        payload, selected_organization, new_input_id_prefix, is_additional_responders_checked, error_msg
    )

    # Add title and message inputs
    blocks: Block.AnyBlocks = [_get_title_input(payload), _get_message_input(payload)]

    # Add organization select if more than one organization available for user
    if len(available_organizations) > 1:
        organization_select = _get_organization_select(
            available_organizations, selected_organization, new_input_id_prefix
        )
        blocks.append(organization_select)

    # Add team select and additional responders blocks
    blocks += team_select_blocks
    blocks += additional_responders_blocks

    return _get_form_view(submit_routing_uid, blocks, json.dumps(new_private_metadata))


def _get_form_view(routing_uid: str, blocks: Block.AnyBlocks, private_metadata: str) -> ModalView:
    view: ModalView = {
        "type": "modal",
        "callback_id": routing_uid,
        "title": {
            "type": "plain_text",
            "text": "Create Alert Group",
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True,
        },
        "submit": {
            "type": "plain_text",
            "text": "Create",
        },
        "blocks": blocks,
        "private_metadata": private_metadata,
    }
    return view


def _get_organization_select(
    organizations: QuerySet["Organization"], value: "Organization", input_id_prefix: str
) -> Block.Input:
    organizations_options: typing.List[CompositionObjectOption] = []
    initial_option_idx = 0
    for idx, org in enumerate(organizations):
        if org == value:
            initial_option_idx = idx
        organizations_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": f"{org.org_title} ({org.stack_slug})",
                    "emoji": True,
                },
                "value": f"{org.pk}",
            }
        )

    organization_select: Block.Input = {
        "type": "input",
        "block_id": input_id_prefix + DIRECT_PAGING_ORG_SELECT_ID,
        "label": {
            "type": "plain_text",
            "text": "Organization",
        },
        "element": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Organization", "emoji": True},
            "options": organizations_options,
            "action_id": OnPagingOrgChange.routing_uid(),
            "initial_option": organizations_options[initial_option_idx],
        },
        "dispatch_action": True,
    }

    return organization_select


def _get_select_field_value(payload: EventPayload, prefix_id: str, routing_uid: str, field_id: str) -> str | None:
    try:
        field = payload["view"]["state"]["values"][prefix_id + field_id][routing_uid]["selected_option"]
    except KeyError:
        return None
    return field["value"] if field else None


def _get_selected_org_from_payload(
    payload: EventPayload,
    input_id_prefix: str,
    slack_team_identity: "SlackTeamIdentity",
    slack_user_identity: "SlackUserIdentity",
) -> typing.Optional["Organization"]:
    from apps.user_management.models import Organization

    selected_org_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingOrgChange.routing_uid(), DIRECT_PAGING_ORG_SELECT_ID
    )
    if selected_org_id is None:
        return _get_available_organizations(slack_team_identity, slack_user_identity).first()
    return Organization.objects.filter(pk=selected_org_id).first()


def _get_team_select_blocks(
    slack_user_identity: "SlackUserIdentity",
    organization: "Organization",
    is_selected: bool,
    value: "Team",
    input_id_prefix: str,
) -> Block.AnyBlocks:
    user = slack_user_identity.get_user(organization)  # TODO: handle None
    teams = user.available_teams

    team_options: typing.List[CompositionObjectOption] = []
    # Adding pseudo option for default team
    initial_option_idx = 0
    team_options.append(
        {
            "text": {
                "type": "plain_text",
                "text": "No team",
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

    team_select: Block.Input = {
        "type": "input",
        "block_id": input_id_prefix + DIRECT_PAGING_TEAM_SELECT_ID,
        "label": {
            "type": "plain_text",
            "text": "Team to notify",
        },
        "element": {
            "type": "static_select",
            "action_id": OnPagingTeamChange.routing_uid(),
            "placeholder": {"type": "plain_text", "text": "Select team", "emoji": True},
            "options": team_options,
        },
        "dispatch_action": True,
    }

    # No context block if no team selected
    if not is_selected:
        return [team_select]

    team_select["element"]["initial_option"] = team_options[initial_option_idx]
    return [team_select, _get_team_select_context(organization, value)]


def _get_team_select_context(organization: "Organization", team: "Team") -> Block.Context:
    team_name = team.name if team else "No team"
    alert_receive_channel = AlertReceiveChannel.objects.filter(
        organization=organization,
        team=team,
        integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
    ).first()

    escalation_chains_exist = EscalationChain.objects.filter(
        channel_filters__alert_receive_channel=alert_receive_channel
    ).exists()

    if not alert_receive_channel:
        context_text = (
            ":warning: *Direct paging integration missing*\n"
            "The selected team doesn't have a direct paging integration configured and will not be notified. "
            "If you proceed with the alert group, an empty direct paging integration will be created automatically for the team. "
            "<https://grafana.com/docs/oncall/latest/integrations/manual/#learn-the-flow-and-handle-warnings|Learn more.>"
        )
    elif not escalation_chains_exist:
        context_text = (
            ":warning: *Direct paging integration not configured*\n"
            "The direct paging integration for the selected team has no escalation chains configured. "
            "If you proceed with the alert group, the team likely will not be notified. "
            "<https://grafana.com/docs/oncall/latest/integrations/manual/#learn-the-flow-and-handle-warnings|Learn more.>"
        )
    else:
        context_text = f"Integration <{alert_receive_channel.web_link}|{alert_receive_channel.verbal_name} ({team_name})> will be used for notification."

    context: Block.Context = {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": context_text,
            }
        ],
    }
    return context


def _get_additional_responders_blocks(
    payload: EventPayload,
    organization: "Organization",
    input_id_prefix,
    is_additional_responders_checked: bool,
    error_msg: str | None,
) -> Block.AnyBlocks:
    checkbox_option: CompositionObjectOption = {
        "text": {
            "type": "plain_text",
            "text": "Notify additional responders",
        },
    }

    blocks: Block.AnyBlocks = [
        typing.cast(
            Block.Input,
            {
                "type": "input",
                "block_id": input_id_prefix + DIRECT_PAGING_ADDITIONAL_RESPONDERS_INPUT_ID,
                "label": {
                    "type": "plain_text",
                    "text": "Additional responders",
                },
                "element": {
                    "type": "checkboxes",
                    "options": [checkbox_option],
                    "action_id": OnPagingCheckAdditionalResponders.routing_uid(),
                },
                "optional": True,
                "dispatch_action": True,
            },
        ),
    ]

    if is_additional_responders_checked:
        blocks[0]["element"]["initial_options"] = [checkbox_option]

    if error_msg:
        blocks += [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "block_id": "error_message",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":warning: {error_msg}",
                    },
                },
            ),
        ]

    if is_additional_responders_checked:
        users_select = _get_users_select(organization, input_id_prefix, OnPagingUserChange.routing_uid())
        schedules_select = _get_schedules_select(organization, input_id_prefix, OnPagingScheduleChange.routing_uid())

        blocks += [users_select, schedules_select]
        # selected items
        selected_users = get_current_items(payload, DataKey.USERS, organization.users)
        selected_schedules = get_current_items(payload, DataKey.SCHEDULES, organization.oncall_schedules)

        if selected_users or selected_schedules:
            blocks += [DIVIDER]
            blocks += _get_selected_entries_list(input_id_prefix, DataKey.USERS, selected_users)
            blocks += _get_selected_entries_list(input_id_prefix, DataKey.SCHEDULES, selected_schedules)
            blocks += [DIVIDER]

    return blocks


def _get_users_select(
    organization: "Organization", input_id_prefix: str, action_id: str, max_options_per_group=MAX_STATIC_SELECT_OPTIONS
) -> Block.Context | Block.Section:
    users = organization.users.all()

    user_options: typing.List[CompositionObjectOption] = [
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
        return typing.cast(
            Block.Context, {"type": "context", "elements": [{"type": "mrkdwn", "text": "No users available"}]}
        )

    user_select: Block.Section = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Notify user"},
        "block_id": input_id_prefix + DIRECT_PAGING_USER_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select user", "emoji": True},
            "action_id": action_id,
        },
    }

    if len(user_options) > max_options_per_group:
        user_select["accessory"]["option_groups"] = _get_option_groups(user_options, max_options_per_group)
    else:
        user_select["accessory"]["options"] = user_options

    return user_select


def _get_schedules_select(
    organization: "Organization", input_id_prefix: str, action_id: str, max_options_per_group=MAX_STATIC_SELECT_OPTIONS
) -> Block.Context | Block.Section:
    schedules = organization.oncall_schedules.all()

    schedule_options: typing.List[CompositionObjectOption] = [
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
        return typing.cast(
            Block.Context,
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "No schedules available"}],
            },
        )

    schedule_select: Block.Section = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Notify schedule"},
        "block_id": input_id_prefix + DIRECT_PAGING_SCHEDULE_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select schedule", "emoji": True},
            "action_id": action_id,
        },
    }

    if len(schedule_options) > max_options_per_group:
        schedule_select["accessory"]["option_groups"] = _get_option_groups(schedule_options, max_options_per_group)
    else:
        schedule_select["accessory"]["options"] = schedule_options

    return schedule_select


def _get_option_groups(
    options: typing.List[CompositionObjectOption], max_options_per_group: int
) -> typing.List[CompositionObjectOptionGroup]:
    chunks = [options[x : x + max_options_per_group] for x in range(0, len(options), max_options_per_group)]

    option_groups: typing.List[CompositionObjectOptionGroup] = []
    for idx, group in enumerate(chunks):
        start = idx * max_options_per_group + 1
        end = idx * max_options_per_group + max_options_per_group
        option_groups.append(
            {
                "label": {"type": "plain_text", "text": f"({start}-{end})"},
                "options": group,
            }
        )

    return option_groups


def _get_selected_entries_list(
    input_id_prefix: str, key: DataKey, entries: typing.List[typing.Tuple[Model, Policy]]
) -> typing.List[Block.Section]:
    current_entries: typing.List[Block.Section] = []
    for entry, policy in entries:
        if key == DataKey.USERS:
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


def _display_availability_warnings(
    payload: EventPayload, warnings: typing.List[AvailabilityWarning], organization: "Organization", user: "User"
) -> ModalView:
    metadata = json.loads(payload["view"]["private_metadata"])
    return _get_availability_warnings_view(
        warnings,
        organization,
        user,
        OnPagingConfirmUserChange.routing_uid(),
        json.dumps(
            {
                "state": payload["view"]["state"],
                "input_id_prefix": metadata["input_id_prefix"],
                "channel_id": metadata["channel_id"],
                "submit_routing_uid": metadata["submit_routing_uid"],
                DataKey.USERS: metadata[DataKey.USERS],
                DataKey.SCHEDULES: metadata[DataKey.SCHEDULES],
            }
        ),
    )


def _get_availability_warnings_view(
    warnings: typing.List[AvailabilityWarning],
    organization: "Organization",
    user: "User",
    callback_id: str,
    private_metadata: str,
) -> ModalView:
    messages: typing.List[str] = []
    for w in warnings:
        if w["error"] == PagingError.USER_IS_NOT_ON_CALL:
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
        elif w["error"] == PagingError.USER_HAS_NO_NOTIFICATION_POLICY:
            messages.append(f":warning: User *{user.name or user.username}* has no notification policy setup.")

    view: ModalView = {
        "type": "modal",
        "callback_id": callback_id,
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
        "private_metadata": private_metadata,
    }
    return view


def _get_selected_team_from_payload(
    payload: EventPayload, input_id_prefix: str
) -> typing.Tuple[str | None, typing.Optional["Team"]]:
    from apps.user_management.models import Team

    selected_team_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingTeamChange.routing_uid(), DIRECT_PAGING_TEAM_SELECT_ID
    )

    if selected_team_id is None:
        return None, None

    if selected_team_id == DEFAULT_TEAM_VALUE:
        return selected_team_id, None

    team = Team.objects.filter(pk=selected_team_id).first()
    return selected_team_id, team


def _get_additional_responders_checked_from_payload(payload: EventPayload, input_id_prefix: str) -> bool:
    try:
        selected_options = payload["view"]["state"]["values"][
            input_id_prefix + DIRECT_PAGING_ADDITIONAL_RESPONDERS_INPUT_ID
        ][OnPagingCheckAdditionalResponders.routing_uid()]["selected_options"]
    except KeyError:
        return False

    return len(selected_options) > 0


def _get_selected_user_from_payload(payload: EventPayload, input_id_prefix: str) -> typing.Optional["User"]:
    from apps.user_management.models import User

    selected_user_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingUserChange.routing_uid(), DIRECT_PAGING_USER_SELECT_ID
    )
    if selected_user_id is not None:
        user = User.objects.filter(pk=selected_user_id).first()
        return user
    return None


def _get_selected_schedule_from_payload(
    payload: EventPayload, input_id_prefix: str
) -> typing.Optional["OnCallSchedule"]:
    from apps.schedules.models import OnCallSchedule

    selected_schedule_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingScheduleChange.routing_uid(), DIRECT_PAGING_SCHEDULE_SELECT_ID
    )
    if selected_schedule_id is not None:
        return OnCallSchedule.objects.filter(pk=selected_schedule_id).first()
    return None


def _get_and_change_input_id_prefix_from_metadata(
    metadata: typing.Dict[str, str]
) -> typing.Tuple[str, str, typing.Dict[str, str]]:
    old_input_id_prefix = metadata["input_id_prefix"]
    new_input_id_prefix = _generate_input_id_prefix()
    metadata["input_id_prefix"] = new_input_id_prefix
    return old_input_id_prefix, new_input_id_prefix, metadata


def _get_title_input(payload: EventPayload) -> Block.Input:
    title_input_block: Block.Input = {
        "type": "input",
        "block_id": DIRECT_PAGING_TITLE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Title",
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


def _get_title_from_payload(payload: EventPayload) -> str:
    title = payload["view"]["state"]["values"][DIRECT_PAGING_TITLE_INPUT_ID][FinishDirectPaging.routing_uid()]["value"]
    return title


def _get_message_input(payload: EventPayload) -> Block.Input:
    message_input_block: Block.Input = {
        "type": "input",
        "block_id": DIRECT_PAGING_MESSAGE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Message",
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


def _get_message_from_payload(payload: EventPayload) -> str:
    return (
        payload["view"]["state"]["values"][DIRECT_PAGING_MESSAGE_INPUT_ID][FinishDirectPaging.routing_uid()]["value"]
        or ""
    )


def _get_available_organizations(
    slack_team_identity: "SlackTeamIdentity", slack_user_identity: "SlackUserIdentity"
) -> QuerySet["Organization"]:
    return (
        slack_team_identity.organizations.filter(users__slack_user_identity=slack_user_identity)
        .order_by("pk")
        .distinct()
    )


# _generate_input_id_prefix returns uniq str to not to preserve input's values between view update
#  https://api.slack.com/methods/views.update#markdown
def _generate_input_id_prefix() -> str:
    return str(uuid4())


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": OnPagingOrgChange.routing_uid(),
        "step": OnPagingOrgChange,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": OnPagingTeamChange.routing_uid(),
        "step": OnPagingTeamChange,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.CHECKBOXES,
        "block_action_id": OnPagingCheckAdditionalResponders.routing_uid(),
        "step": OnPagingCheckAdditionalResponders,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": OnPagingUserChange.routing_uid(),
        "step": OnPagingUserChange,
    },
    {
        "payload_type": PayloadType.VIEW_SUBMISSION,
        "view_callback_id": OnPagingConfirmUserChange.routing_uid(),
        "step": OnPagingConfirmUserChange,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": OnPagingScheduleChange.routing_uid(),
        "step": OnPagingScheduleChange,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.OVERFLOW,
        "block_action_id": OnPagingItemActionChange.routing_uid(),
        "step": OnPagingItemActionChange,
    },
    {
        "payload_type": PayloadType.SLASH_COMMAND,
        "command_name": StartDirectPaging.command_name,
        "step": StartDirectPaging,
    },
    {
        "payload_type": PayloadType.VIEW_SUBMISSION,
        "view_callback_id": FinishDirectPaging.routing_uid(),
        "step": FinishDirectPaging,
    },
]
