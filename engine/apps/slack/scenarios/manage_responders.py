import json
import typing

from apps.alerts.paging import DirectPagingAlertGroupResolvedError, direct_paging, unpage_user, user_is_oncall
from apps.slack.chatops_proxy_routing import make_private_metadata, make_value
from apps.slack.constants import DIVIDER
from apps.slack.scenarios import scenario_step
from apps.slack.scenarios.paging import (
    DIRECT_PAGING_USER_SELECT_ID,
    _display_confirm_participant_invitation_view,
    _generate_input_id_prefix,
    _get_select_field_value,
    _get_users_select,
)
from apps.slack.scenarios.step_mixins import AlertGroupActionsMixin
from apps.slack.types import Block, BlockActionType, EventPayload, ModalView, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.user_management.models import User

MANAGE_RESPONDERS_USER_SELECT_ID = "responders_user_select"

USER_DATA_KEY = "user"
ALERT_GROUP_DATA_KEY = "alert_group_pk"

# Slack scenario steps


class StartManageResponders(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    """Handle "Responders" button click."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        view = render_dialog(alert_group)
        self._slack_client.views_open(trigger_id=payload["trigger_id"], view=view)


class ManageRespondersUserChange(scenario_step.ScenarioStep):
    """Handle user selection in responders modal."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        organization = alert_group.channel.organization

        # check if user is on-call
        if not user_is_oncall(selected_user):
            # display additional confirmation modal
            private_metadata = make_private_metadata(
                {USER_DATA_KEY: selected_user.id, ALERT_GROUP_DATA_KEY: alert_group.pk}, organization
            )
            view = _display_confirm_participant_invitation_view(
                ManageRespondersConfirmUserChange.routing_uid(), private_metadata
            )

            self._slack_client.views_push(trigger_id=payload["trigger_id"], view=view)
        else:
            try:
                # no warnings, proceed with paging
                direct_paging(
                    organization=organization,
                    from_user=slack_user_identity.get_user(organization),
                    message=None,  # reuse the message from the original alert
                    team=alert_group.channel.team,
                    users=[(selected_user, False)],
                    alert_group=alert_group,
                )
                view = render_dialog(alert_group)
            except DirectPagingAlertGroupResolvedError:
                view = render_dialog(alert_group, alert_group_resolved_warning=True)

            self._slack_client.views_update(
                trigger_id=payload["trigger_id"],
                view=view,
                view_id=payload["view"]["id"],
            )


class ManageRespondersConfirmUserChange(scenario_step.ScenarioStep):
    """Handle user confirmation on availability warnings modal."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        organization = alert_group.channel.organization

        try:
            direct_paging(
                organization=organization,
                from_user=slack_user_identity.get_user(organization),
                message=None,  # reuse the message from the original alert
                team=alert_group.channel.team,
                users=[(selected_user, False)],
                alert_group=alert_group,
            )
            view = render_dialog(alert_group)
        except DirectPagingAlertGroupResolvedError:
            view = render_dialog(alert_group, alert_group_resolved_warning=True)

        self._slack_client.views_update(
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["previous_view_id"],
        )


class ManageRespondersRemoveUser(scenario_step.ScenarioStep):
    """Handle user removal in responders modal."""

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        alert_group = _get_alert_group_from_payload(payload)
        selected_user = _get_selected_user_from_payload(payload)
        from_user = slack_user_identity.get_user(alert_group.channel.organization)

        unpage_user(alert_group, selected_user, from_user)
        view = render_dialog(alert_group)
        self._slack_client.views_update(
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


# slack view/blocks rendering helpers


def render_dialog(alert_group: "AlertGroup", alert_group_resolved_warning=False) -> ModalView:
    blocks: Block.AnyBlocks = []

    # Show list of users that are currently paged
    paged_users = alert_group.get_paged_users()
    for user in alert_group.get_paged_users():
        blocks += [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":bust_in_silhouette: *{user['name'] or user['username']}*"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Remove", "emoji": True},
                        "action_id": ManageRespondersRemoveUser.routing_uid(),
                        "value": make_value({"id": str(user["id"])}, alert_group.channel.organization),
                    },
                },
            ),
        ]
    if paged_users:
        blocks += [DIVIDER]

    # Show a warning when trying to add responders for a resolved alert group
    if alert_group_resolved_warning:
        blocks += [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":no_entry: {DirectPagingAlertGroupResolvedError.DETAIL}"},
                },
            ),
        ]

    # Show user dropdown
    input_id_prefix = _generate_input_id_prefix()
    blocks.append(
        _get_users_select(alert_group.channel.organization, input_id_prefix, ManageRespondersUserChange.routing_uid())
    )

    view: ModalView = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Additional responders",
        },
        "blocks": blocks,
        "private_metadata": json.dumps({ALERT_GROUP_DATA_KEY: alert_group.pk, "input_id_prefix": input_id_prefix}),
    }
    return view


def _get_selected_user_from_payload(payload: EventPayload) -> "User":
    from apps.user_management.models import User

    try:
        selected_user_id = json.loads(payload["actions"][0]["value"])["id"]  # "remove" button
    except KeyError:
        try:
            # "confirm" button on availability warnings modal
            selected_user_id = json.loads(payload["view"]["private_metadata"])[USER_DATA_KEY]
        except KeyError:
            # user select dropdown
            input_id_prefix = json.loads(payload["view"]["private_metadata"])["input_id_prefix"]
            selected_user_id = _get_select_field_value(
                payload, input_id_prefix, ManageRespondersUserChange.routing_uid(), DIRECT_PAGING_USER_SELECT_ID
            )

    return User.objects.get(pk=selected_user_id)


def _get_alert_group_from_payload(payload: EventPayload) -> "AlertGroup":
    from apps.alerts.models import AlertGroup

    alert_group_pk = json.loads(payload["view"]["private_metadata"])[ALERT_GROUP_DATA_KEY]
    return AlertGroup.objects.get(pk=alert_group_pk)


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": ManageRespondersUserChange.routing_uid(),
        "step": ManageRespondersUserChange,
    },
    {
        "payload_type": PayloadType.VIEW_SUBMISSION,
        "view_callback_id": ManageRespondersConfirmUserChange.routing_uid(),
        "step": ManageRespondersConfirmUserChange,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": ManageRespondersRemoveUser.routing_uid(),
        "step": ManageRespondersRemoveUser,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": StartManageResponders.routing_uid(),
        "step": StartManageResponders,
    },
]
