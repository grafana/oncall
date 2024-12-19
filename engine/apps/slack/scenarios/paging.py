import enum
import json
import logging
import typing
from uuid import uuid4

from django.conf import settings
from django.db.models import Model, QuerySet
from rest_framework.response import Response

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.paging import DirectPagingUserTeamValidationError, UserNotifications, direct_paging, user_is_oncall
from apps.api.permissions import RBACPermission, user_is_authorized
from apps.grafana_plugin.ui_url_builder import UIURLBuilder
from apps.schedules.ical_utils import get_cached_oncall_users_for_multiple_schedules
from apps.slack.chatops_proxy_routing import make_private_metadata, make_value
from apps.slack.constants import DIVIDER, PRIVATE_METADATA_MAX_LENGTH
from apps.slack.errors import SlackAPIChannelNotFoundError, SlackAPIError
from apps.slack.scenarios import scenario_step
from apps.slack.slash_command import SlashCommand
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

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.user_management.models import Organization, Team, User

DIRECT_PAGING_TEAM_SELECT_ID = "paging_team_select"
DIRECT_PAGING_TEAM_SEVERITY_CHECKBOXES_ID = "paging_team_severity_checkboxes"
DIRECT_PAGING_ORG_SELECT_ID = "paging_org_select"
DIRECT_PAGING_USER_SELECT_ID = "paging_user_select"
DIRECT_PAGING_MESSAGE_INPUT_ID = "paging_message_input"

DIRECT_PAGING_TEAM_SEVERITY_CHECKBOX_VALUE = "important"

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


# helpers to manage current selected users state


class DataKey(enum.StrEnum):
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
    for key in (DataKey.USERS,):
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

    @staticmethod
    def matcher(slash_command: SlashCommand) -> bool:
        # Check if command is /escalate. It's a legacy command we keep for smooth transition.
        is_legacy_command = slash_command.command == settings.SLACK_DIRECT_PAGING_SLASH_COMMAND
        # Check if command is /grafana escalate. It's a new command from unified app.
        is_unified_app_command = slash_command.is_root_command and slash_command.subcommand == "escalate"
        return is_legacy_command or is_unified_app_command

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        input_id_prefix = _generate_input_id_prefix()

        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        if settings.UNIFIED_SLACK_APP_ENABLED:
            if slack_team_identity.needs_reinstall:
                organizations = _get_available_organizations(slack_team_identity, slack_user_identity)
                if len(organizations) == 1:
                    # Provide a link to web if user has access only to one organization
                    link = UIURLBuilder(organizations[0]).settings("?tab=ChatOps&chatOpsTab=Slack")
                else:
                    # Otherwise, provide a link to the documentation
                    link = (
                        "https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations"
                        "/references/slack/#migrate-to-the-grafana-irm-slack-integration"
                    )
                upgrade = f"<{link}|Upgrade>"
                msg = (
                    f"The new Slack IRM integration is now available. f{upgrade} for a more powerful and flexible "
                    f"way to interact with Grafana IRM on Slack."
                )
                try:
                    self._slack_client.chat_postEphemeral(
                        channel=channel_id, user=slack_user_identity.slack_id, text=msg
                    )
                except SlackAPIError:
                    # catch all exceptions to prevent the slash command from failing
                    logger.warning("StartDirectPaging: failed to send ephemeral message to user", exc_info=True)
            else:
                # hack, parsing command again to determine if it's a legacy command
                cmd = SlashCommand.parse(payload)
                is_legacy_command = cmd.command == settings.SLACK_DIRECT_PAGING_SLASH_COMMAND
                if is_legacy_command:
                    self._slack_client.chat_postEphemeral(
                        channel=channel_id,
                        user=slack_user_identity.slack_id,
                        text=f"The new Slack IRM integration is now available. "
                        f"Please use `/{settings.SLACK_IRM_ROOT_COMMAND}` escalate to complete the action",
                    )
                    return

        private_metadata = {
            "channel_id": channel_id,
            "input_id_prefix": input_id_prefix,
            "submit_routing_uid": FinishDirectPaging.routing_uid(),
            DataKey.USERS: {},
        }
        # We have access to predefined org only in StartDirectPaging, since it's a slash command.
        # Chatops-Proxy adds a special header to slash commands payload to define the organization.
        # Other Paging steps are triggered by buttons and actions,
        # so we don't have access to predefined org and use private metadata instead.
        private_metadata = _inject_predefined_org_to_private_metadata(predefined_org, private_metadata)
        initial_payload = {"view": {"private_metadata": json.dumps(private_metadata)}}
        view = render_dialog(slack_user_identity, slack_team_identity, initial_payload, initial=True)
        self._slack_client.views_open(
            trigger_id=payload["trigger_id"],
            view=view,
        )


class FinishDirectPaging(scenario_step.ScenarioStep):
    """Handle page command dialog submit."""

    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_DIRECT_PAGING]

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        message = _get_message_from_payload(payload)
        private_metadata = json.loads(payload["view"]["private_metadata"])
        predefined_org = _get_predefined_org_from_private_metadata(private_metadata, slack_team_identity)
        channel_id = private_metadata["channel_id"]
        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = predefined_org or _get_selected_org_from_payload(
            payload, input_id_prefix, slack_team_identity, slack_user_identity
        )

        # get user in the context of the selected_organization
        user = slack_user_identity.get_user(selected_organization)
        if not user_is_authorized(user, self.REQUIRED_PERMISSIONS):
            unauthorized_error = _get_unauthorized_warning(error=True)
            return Response(
                {
                    "response_action": "update",
                    "view": render_dialog(
                        slack_user_identity, slack_team_identity, payload, validation_errors=unauthorized_error
                    ),
                },
                status=200,
            )

        _, selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        user = slack_user_identity.get_user(selected_organization)

        selected_users: UserNotifications = [
            (u, p == Policy.IMPORTANT)
            for u, p in get_current_items(payload, DataKey.USERS, selected_organization.users)
        ]

        # trigger direct paging to selected team + users
        try:
            alert_group = direct_paging(
                organization=selected_organization,
                from_user=user,
                message=message,
                team=selected_team,
                important_team_escalation=_get_team_escalation_severity_from_payload(payload, input_id_prefix),
                users=selected_users,
            )
        except DirectPagingUserTeamValidationError:
            # show validation warning messages
            validation_errors: Block.AnyBlocks = [
                typing.cast(
                    Block.Section,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":warning: At least one team or one user must be selected to directly page",
                        },
                    },
                )
            ]

            return Response(
                {
                    "response_action": "update",
                    "view": render_dialog(
                        slack_user_identity, slack_team_identity, payload, validation_errors=validation_errors
                    ),
                },
                status=200,
            )

        text = f":white_check_mark: Escalation created: {alert_group.web_link}"

        try:
            self._slack_client.chat_postEphemeral(
                channel=channel_id,
                user=slack_user_identity.slack_id,
                text=text,
            )
        except SlackAPIChannelNotFoundError:
            self._slack_client.chat_postEphemeral(
                channel=slack_user_identity.im_channel_id,
                user=slack_user_identity.slack_id,
                text=text,
            )


# OnChange steps, responsible for rerendering form on changed values


class OnPagingOrgChange(scenario_step.ScenarioStep):
    """Reload form with updated organization."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        updated_payload = reset_items(payload)
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload)
        self._slack_client.views_update(
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
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        view = render_dialog(slack_user_identity, slack_team_identity, payload)
        self._slack_client.views_update(
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnPagingTeamSeverityCheckboxChange(OnPagingTeamChange):
    """
    Specify alert severity when escalating to a team.

    NOTE: we simply reuse `OnPagingTeamChange` step, since the behavior is the same.
    """


class OnPagingUserChange(scenario_step.ScenarioStep):
    """Add selected to user to the list.

    It will check to see if the user is on-call, pushing a new modal for additional confirmation if needed.
    """

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        private_metadata = json.loads(payload["view"]["private_metadata"])
        selected_user = _get_selected_user_from_payload(payload, private_metadata["input_id_prefix"])
        if selected_user is None:
            return

        # check if user is on-call
        if not user_is_oncall(selected_user):
            # display additional confirmation modal
            metadata = json.loads(payload["view"]["private_metadata"])
            private_metadata = {
                "state": payload["view"]["state"],
                "input_id_prefix": metadata["input_id_prefix"],
                "channel_id": metadata["channel_id"],
                "submit_routing_uid": metadata["submit_routing_uid"],
                DataKey.USERS: metadata[DataKey.USERS],
            }
            # keep predefined organization in private metadata
            if "organization_id" in metadata:
                private_metadata["organization_id"] = metadata["organization_id"]

            view = _display_confirm_participant_invitation_view(
                OnPagingConfirmUserChange.routing_uid(),
                make_private_metadata(private_metadata, selected_user.organization),
            )
            self._slack_client.views_push(trigger_id=payload["trigger_id"], view=view)
        else:
            # user is currently on-call
            error_msg = None
            try:
                policy = Policy.DEFAULT
                if selected_user.organization.direct_paging_prefer_important_policy:
                    policy = Policy.IMPORTANT
                updated_payload = add_or_update_item(payload, DataKey.USERS, selected_user.pk, policy)
            except ValueError:
                updated_payload = payload
                error_msg = "Cannot add user, maximum responders exceeded"
            view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
            self._slack_client.views_update(
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class OnPagingItemActionChange(scenario_step.ScenarioStep):
    """Reload form with updated user details."""

    def _parse_action(self, payload: EventPayload) -> typing.Tuple[Policy, DataKey, str]:
        value = json.loads(payload["actions"][0]["selected_option"]["value"])
        return value["action"], value["key"], value["id"]

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
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
        self._slack_client.views_update(trigger_id=payload["trigger_id"], view=view, view_id=payload["view"]["id"])


class OnPagingConfirmUserChange(scenario_step.ScenarioStep):
    """Confirm user selection despite not being on-call."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        metadata = json.loads(payload["view"]["private_metadata"])

        # recreate original view state and metadata
        private_metadata = {
            "channel_id": metadata["channel_id"],
            "input_id_prefix": metadata["input_id_prefix"],
            "submit_routing_uid": metadata["submit_routing_uid"],
            DataKey.USERS: metadata[DataKey.USERS],
        }
        # keep predefined organization in private metadata
        if "organization_id" in metadata:
            private_metadata["organization_id"] = metadata["organization_id"]

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
            policy = Policy.DEFAULT
            if selected_user.organization.direct_paging_prefer_important_policy:
                policy = Policy.IMPORTANT
            updated_payload = add_or_update_item(previous_view_payload, DataKey.USERS, selected_user.pk, policy)
        except ValueError:
            updated_payload = payload
            error_msg = "Cannot add user, maximum responders exceeded"
        view = render_dialog(slack_user_identity, slack_team_identity, updated_payload, error_msg=error_msg)
        self._slack_client.views_update(
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["previous_view_id"],
        )


# slack view/blocks rendering helpers


def render_dialog(
    slack_user_identity: "SlackUserIdentity",
    slack_team_identity: "SlackTeamIdentity",
    payload: EventPayload,
    initial=False,
    error_msg=None,
    validation_errors: typing.Optional[Block.AnyBlocks] = None,
) -> ModalView:
    private_metadata = json.loads(payload["view"]["private_metadata"])
    submit_routing_uid = private_metadata.get("submit_routing_uid")

    predefined_org = _get_predefined_org_from_private_metadata(private_metadata, slack_team_identity)
    available_organizations = _get_available_organizations(slack_team_identity, slack_user_identity)

    if initial:
        # setup initial form
        new_input_id_prefix = _generate_input_id_prefix()
        new_private_metadata = private_metadata
        new_private_metadata["input_id_prefix"] = new_input_id_prefix
        selected_organization = predefined_org if predefined_org else available_organizations.first()
        is_team_selected, selected_team = False, None
        is_team_escalation_important = False
    else:
        # setup form using data/state
        old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
            private_metadata
        )
        selected_organization = (
            predefined_org
            if predefined_org
            else _get_selected_org_from_payload(payload, old_input_id_prefix, slack_team_identity, slack_user_identity)
        )
        is_team_selected, selected_team = _get_selected_team_from_payload(payload, old_input_id_prefix)
        is_team_escalation_important = _get_team_escalation_severity_from_payload(payload, old_input_id_prefix)

    blocks: Block.AnyBlocks = []

    if validation_errors:
        blocks += validation_errors

    # get user in the context of the selected_organization
    user = slack_user_identity.get_user(selected_organization)
    if not user_is_authorized(user, FinishDirectPaging.REQUIRED_PERMISSIONS):
        blocks += _get_unauthorized_warning()

    blocks.append(_get_message_input(payload))

    # Add organization select if org is not defined on chatops-proxy (it's should happen only in OSS)
    # and user has access to multiple orgs.
    if not predefined_org and len(available_organizations) > 1:
        organization_select = _get_organization_select(
            available_organizations, selected_organization, new_input_id_prefix
        )
        blocks.append(organization_select)

    # Add team select/severity and additional responders blocks
    blocks += _get_team_select_blocks(
        slack_user_identity,
        selected_organization,
        is_team_selected,
        selected_team,
        is_team_escalation_important,
        new_input_id_prefix,
    )
    blocks += _get_user_select_blocks(payload, selected_organization, new_input_id_prefix, error_msg)

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*Note*: you *must* specify at least one team or one user to directly page.",
                },
            ],
        }
    )

    return _get_form_view(
        submit_routing_uid, blocks, make_private_metadata(new_private_metadata, selected_organization)
    )


def _get_unauthorized_warning(error=False):
    icon = ":warning:" if not error else ":no_entry:"
    text = f"{icon} You do not have permission to perform this action."
    if not error:
        text += "\nAsk an admin to upgrade your permissions."
    return [
        typing.cast(
            Block.Section,
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        )
    ]


def _get_form_view(routing_uid: str, blocks: Block.AnyBlocks, private_metadata: str) -> ModalView:
    view: ModalView = {
        "type": "modal",
        "callback_id": routing_uid,
        "title": {
            "type": "plain_text",
            "text": "Create Escalation",
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
                "value": make_value({"id": org.pk}, org),
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
    return json.loads(field["value"])["id"] if field else None


def _get_first_selected_checkbox_option_value(
    payload: EventPayload,
    prefix_id: str,
    routing_uid: str,
    field_id: str,
) -> str | None:
    """
    NOTE: if reusing this for other logic outside of the team severity checkboxes, note that this function
    will only return the value of the first checkbox option...
    """
    try:
        selected_options = payload["view"]["state"]["values"][prefix_id + field_id][routing_uid]["selected_options"]
        if not selected_options:
            return None
        return selected_options[0]["value"]
    except KeyError:
        return None


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


def _inject_predefined_org_to_private_metadata(
    predefined_org: typing.Optional["Organization"], private_metadata: dict
) -> dict:
    """
    Injects predefined organization to private metadata.
    Predefined org is org defined by chatops-proxy for slash commands.
    """
    if predefined_org:
        private_metadata["organization_id"] = predefined_org.pk
    return private_metadata


def _get_predefined_org_from_private_metadata(
    private_metadata: dict,
    slack_team_identity: "SlackTeamIdentity",
) -> typing.Optional["Organization"]:
    """
    Returns organization from private metadata.
    """
    org_id = private_metadata.get("organization_id")
    if not org_id:
        return None

    return slack_team_identity.organizations.filter(pk=org_id).first()


def _get_team_select_blocks(
    slack_user_identity: "SlackUserIdentity",
    organization: "Organization",
    is_selected: bool,
    value: typing.Optional["Team"],
    is_team_escalation_important: bool,
    input_id_prefix: str,
) -> Block.AnyBlocks:
    blocks: Block.AnyBlocks = []
    user = slack_user_identity.get_user(organization)  # TODO: handle None
    teams = (
        user.organization.get_notifiable_direct_paging_integrations()
        .filter(team__isnull=False)
        .values_list("team__pk", "team__name")
    )

    direct_paging_info_msg = {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": (
                    "*Note*: You can only page teams which have a Direct Paging integration that is configured. "
                    "<https://grafana.com/docs/oncall/latest/integrations/manual/#set-up-direct-paging-for-a-team|Learn more>"
                ),
            },
        ],
    }

    if not teams:
        direct_paging_info_msg["elements"][0][
            "text"
        ] += ".\n\nThere are currently no teams which have a Direct Paging integration that is configured."
        blocks.append(direct_paging_info_msg)
        return blocks

    team_options: typing.List[CompositionObjectOption] = []

    initial_option_idx = 0
    for idx, team in enumerate(teams):
        team_pk, team_name = team

        if value and value.pk == team_pk:
            initial_option_idx = idx
        team_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": team_name,
                    "emoji": True,
                },
                "value": make_value({"id": team_pk}, organization),
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
        "optional": True,
    }

    blocks.append(team_select)

    # No context block if no team selected
    if not is_selected:
        blocks.append(direct_paging_info_msg)
        return blocks

    team_select["element"]["initial_option"] = team_options[initial_option_idx]

    alert_receive_channel = AlertReceiveChannel.objects.filter(
        organization=organization,
        team=value,
        integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
    ).first()

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Integration <{alert_receive_channel.web_link}|{alert_receive_channel.verbal_name}> will be used for notification.",
                },
            ],
        }
    )

    team_severity_important_checkbox_option: CompositionObjectOption = {
        "text": {
            "type": "mrkdwn",
            "text": "Important escalation",
        },
        "value": DIRECT_PAGING_TEAM_SEVERITY_CHECKBOX_VALUE,
    }

    team_severity_checkboxes_element: Block.Section = {
        "type": "section",
        "block_id": input_id_prefix + DIRECT_PAGING_TEAM_SEVERITY_CHECKBOXES_ID,
        "text": {
            "type": "plain_text",
            # NOTE: this is a bit of a hack. Slack requires us to specify this text object, and it cannot be empty
            # hence the empty space. We do this so that we can render the text instead in a context block below
            # (which allows us to render it in a slightly smaller font size)
            # https://api.slack.com/reference/block-kit/blocks#section
            "text": " ",
        },
        "accessory": {
            "type": "checkboxes",
            "options": [team_severity_important_checkbox_option],
            "action_id": OnPagingTeamSeverityCheckboxChange.routing_uid(),
        },
    }

    if is_team_escalation_important:
        # From the docs https://api.slack.com/reference/block-kit/block-elements#checkboxes__fields
        # An array of option objects that EXACTLY matches one or more of the options within options
        team_severity_checkboxes_element["accessory"]["initial_options"] = [team_severity_important_checkbox_option]

    blocks.extend(
        [
            team_severity_checkboxes_element,
            typing.cast(
                Block.Context,
                {
                    # NOTE: we add this here instead of as a checkbox option description because those can only
                    # be defined as plain text (ie. not markdown where links are supported)
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                "Check the above box if you would like to escalate to this team as an 'important' "
                                "escalation. Teams can configure their Direct Paging Integration to route to different "
                                "escalation chains based on this. "
                                "<https://grafana.com/docs/oncall/latest/integrations/manual/#important-escalations|Learn more>"
                            ),
                        },
                    ],
                },
            ),
        ]
    )

    return blocks


def _create_user_option_groups(
    organization, users: "RelatedManager['User']", max_options_per_group: int, option_group_label_text_prefix: str
) -> typing.List[CompositionObjectOptionGroup]:
    user_options: typing.List[CompositionObjectOption] = [
        {
            "text": {
                "type": "plain_text",
                "text": f"{user.name or user.username}",
                "emoji": True,
            },
            "value": json.dumps({"id": user.pk}),
        }
        for user in users
    ]

    chunks = [user_options[x : x + max_options_per_group] for x in range(0, len(user_options), max_options_per_group)]
    has_more_than_one_chunk = len(chunks) > 1

    option_groups: typing.List[CompositionObjectOptionGroup] = []
    for idx, group in enumerate(chunks):
        start = idx * max_options_per_group + 1
        end = idx * max_options_per_group + max_options_per_group

        if has_more_than_one_chunk:
            label_text = f"{option_group_label_text_prefix} ({start}-{end})"
        else:
            label_text = option_group_label_text_prefix

        option_groups.append(
            {
                "label": {"type": "plain_text", "text": label_text},
                "options": group,
            }
        )

    # Only inject chatops-proxy metadata into the first dropdown option to reduce payload size
    # so the 250kb Slack limit is not exceeded for orgs with many users
    if option_groups:
        option_groups[0]["options"][0]["value"] = make_value(
            json.loads(option_groups[0]["options"][0]["value"]), organization
        )

    return option_groups


def _get_user_select_blocks(
    payload: EventPayload,
    organization: "Organization",
    input_id_prefix: str,
    error_msg: str | None,
) -> Block.AnyBlocks:
    blocks: Block.AnyBlocks = []

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

    blocks.append(_get_users_select(organization, input_id_prefix, OnPagingUserChange.routing_uid()))

    # selected items
    if selected_users := get_current_items(payload, DataKey.USERS, organization.users):
        blocks += [DIVIDER]
        blocks += _get_selected_entries_list(organization, input_id_prefix, DataKey.USERS, selected_users)
        blocks += [DIVIDER]

    return blocks


def _get_users_select(
    organization: "Organization", input_id_prefix: str, action_id: str, max_options_per_group=MAX_STATIC_SELECT_OPTIONS
) -> Block.Context | Block.Input:
    schedules = get_cached_oncall_users_for_multiple_schedules(organization.oncall_schedules.all())
    oncall_user_pks = {user.pk for _, users in schedules.items() for user in users}

    oncall_user_option_groups = _create_user_option_groups(
        organization, organization.users.filter(pk__in=oncall_user_pks), max_options_per_group, "On-call now"
    )
    not_oncall_user_option_groups = _create_user_option_groups(
        organization, organization.users.exclude(pk__in=oncall_user_pks), max_options_per_group, "Not on-call"
    )

    if not oncall_user_option_groups and not not_oncall_user_option_groups:
        return {"type": "context", "elements": [{"type": "mrkdwn", "text": "No users available"}]}
    return {
        "type": "input",
        "block_id": input_id_prefix + DIRECT_PAGING_USER_SELECT_ID,
        "label": {
            "type": "plain_text",
            "text": "User(s) to notify",
        },
        "element": {
            "type": "static_select",
            "action_id": action_id,
            "placeholder": {"type": "plain_text", "text": "Select user", "emoji": True},
            "option_groups": oncall_user_option_groups + not_oncall_user_option_groups,
        },
        "dispatch_action": True,
        "optional": True,
    }


def _get_selected_entries_list(
    organization: "Organization", input_id_prefix: str, key: DataKey, entries: typing.List[typing.Tuple[Model, Policy]]
) -> typing.List[Block.Section]:
    current_entries: typing.List[Block.Section] = []
    for entry, policy in entries:
        if key == DataKey.USERS:
            icon = ":bust_in_silhouette:"
            name = entry.name or entry.username
            extra = entry.timezone

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
                        {
                            "text": {"type": "plain_text", "text": f"{label}"},
                            "value": make_value({"action": action, "key": key, "id": str(entry.pk)}, organization),
                        }
                        for (action, label) in ITEM_ACTIONS
                    ],
                    "action_id": OnPagingItemActionChange.routing_uid(),
                },
            }
        )
    return current_entries


def _display_confirm_participant_invitation_view(callback_id: str, private_metadata: str) -> ModalView:
    return {
        "type": "modal",
        "callback_id": callback_id,
        "title": {"type": "plain_text", "text": "Confirm user invitation"},
        "submit": {"type": "plain_text", "text": "Confirm"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This user is not currently on-call. We don't recommend to page users outside on-call hours.",
                },
            }
        ],
        "private_metadata": private_metadata,
    }


def _get_selected_team_from_payload(
    payload: EventPayload, input_id_prefix: str
) -> typing.Tuple[str | None, typing.Optional["Team"]]:
    from apps.user_management.models import Team

    selected_team_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingTeamChange.routing_uid(), DIRECT_PAGING_TEAM_SELECT_ID
    )

    if selected_team_id is None:
        return None, None
    return selected_team_id, Team.objects.filter(pk=selected_team_id).first()


def _get_team_escalation_severity_from_payload(payload: EventPayload, input_id_prefix: str) -> bool:
    checkbox_value = _get_first_selected_checkbox_option_value(
        payload,
        input_id_prefix,
        OnPagingTeamSeverityCheckboxChange.routing_uid(),
        DIRECT_PAGING_TEAM_SEVERITY_CHECKBOXES_ID,
    )
    return checkbox_value == DIRECT_PAGING_TEAM_SEVERITY_CHECKBOX_VALUE


def _get_selected_user_from_payload(payload: EventPayload, input_id_prefix: str) -> typing.Optional["User"]:
    from apps.user_management.models import User

    selected_user_id = _get_select_field_value(
        payload, input_id_prefix, OnPagingUserChange.routing_uid(), DIRECT_PAGING_USER_SELECT_ID
    )
    if selected_user_id is not None:
        user = User.objects.filter(pk=selected_user_id).first()
        return user
    return None


def _get_and_change_input_id_prefix_from_metadata(
    metadata: typing.Dict[str, str]
) -> typing.Tuple[str, str, typing.Dict[str, str]]:
    old_input_id_prefix = metadata["input_id_prefix"]
    new_input_id_prefix = _generate_input_id_prefix()
    metadata["input_id_prefix"] = new_input_id_prefix
    return old_input_id_prefix, new_input_id_prefix, metadata


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
        "optional": False,
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


def _generate_input_id_prefix() -> str:
    """
    returns unique string to not preserve input's values between view update

    https://api.slack.com/methods/views.update#markdown
    """
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
        "block_action_id": OnPagingTeamSeverityCheckboxChange.routing_uid(),
        "step": OnPagingTeamSeverityCheckboxChange,
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
        "block_action_type": BlockActionType.OVERFLOW,
        "block_action_id": OnPagingItemActionChange.routing_uid(),
        "step": OnPagingItemActionChange,
    },
    {
        "payload_type": PayloadType.SLASH_COMMAND,
        "step": StartDirectPaging,
        "matcher": StartDirectPaging.matcher,
    },
    {
        "payload_type": PayloadType.VIEW_SUBMISSION,
        "view_callback_id": FinishDirectPaging.routing_uid(),
        "step": FinishDirectPaging,
    },
]
