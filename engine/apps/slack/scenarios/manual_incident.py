import json
from uuid import uuid4

from django.apps import apps
from django.conf import settings

from apps.alerts.models import AlertReceiveChannel
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException

MANUAL_INCIDENT_TEAM_SELECT_ID = "manual_incident_team_select"
MANUAL_INCIDENT_ORG_SELECT_ID = "manual_incident_org_select"
MANUAL_INCIDENT_ROUTE_SELECT_ID = "manual_incident_route_select"
MANUAL_INCIDENT_TITLE_INPUT_ID = "manual_incident_title_input"
MANUAL_INCIDENT_MESSAGE_INPUT_ID = "manual_incident_message_input"

DEFAULT_TEAM_VALUE = "default_team"


class StartCreateIncidentFromMessage(scenario_step.ScenarioStep):
    """
    StartCreateIncidentFromMessage triggers creation of a manual incident from the slack message via submenu
    """

    callback_id = [
        "incident_create",
        "incident_create_staging",
        "incident_create_develop",
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        input_id_prefix = _generate_input_id_prefix()

        channel_id = payload["channel"]["id"]
        try:
            image_url = payload["message"]["files"][0]["permalink"]
        except KeyError:
            image_url = None
        private_metadata = {
            "channel_id": channel_id,
            "image_url": image_url,
            "message": {
                "user": payload["message"].get("user"),
                "text": payload["message"].get("text"),
                "ts": payload["message"].get("ts"),
            },
            "input_id_prefix": input_id_prefix,
            "with_title_and_message_inputs": False,
            "submit_routing_uid": FinishCreateIncidentFromMessage.routing_uid(),
        }

        blocks = _get_manual_incident_initial_form_fields(
            slack_team_identity, slack_user_identity, input_id_prefix, payload
        )
        view = _get_manual_incident_form_view(
            FinishCreateIncidentFromMessage.routing_uid(), blocks, json.dumps(private_metadata)
        )
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class FinishCreateIncidentFromMessage(scenario_step.ScenarioStep):
    """
    FinishCreateIncidentFromMessage creates a manual incident from the slack message via submenu
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        Alert = apps.get_model("alerts", "Alert")

        private_metadata = json.loads(payload["view"]["private_metadata"])

        channel_id = private_metadata["channel_id"]

        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = _get_selected_org_from_payload(payload, input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        selected_route = _get_selected_route_from_payload(payload, input_id_prefix)

        user = slack_user_identity.get_user(selected_organization)
        alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
            organization=selected_organization,
            team=selected_team,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={
                "author": user,
                "verbal_name": f"Manual incidents ({selected_team.name if selected_team else 'General'} team)",
            },
        )

        author_username = slack_user_identity.slack_verbal
        try:
            permalink = self._slack_client.api_call(
                "chat.getPermalink",
                channel=private_metadata["channel_id"],
                message_ts=private_metadata["message"]["ts"],
            )
            permalink = permalink.get("permalink", None)
        except SlackAPIException:
            permalink = None
        title = "Message from {}".format(author_username)
        message = private_metadata["message"]["text"]

        # Deprecated, use custom oncall property instead.
        # update private metadata in payload to use it in alert rendering
        payload["view"]["private_metadata"] = private_metadata
        payload["view"]["private_metadata"]["author_username"] = author_username
        # Custom oncall property in payload to simplify rendering
        payload["oncall"] = {}
        payload["oncall"]["title"] = title
        payload["oncall"]["message"] = message
        payload["oncall"]["author_username"] = author_username
        payload["oncall"]["permalink"] = permalink
        Alert.create(
            title=title,
            message=message,
            image_url=private_metadata["image_url"],
            # Link to the slack message is not here bc it redirects to browser
            link_to_upstream_details=None,
            alert_receive_channel=alert_receive_channel,
            raw_request_data=payload,
            integration_unique_data={"created_by": user.get_username_with_slack_verbal()},
            force_route_id=selected_route.pk,
        )

        try:
            self._slack_client.api_call(
                "chat.postEphemeral",
                channel=channel_id,
                user=slack_user_identity.slack_id,
                text=":white_check_mark: Alert successfully submitted",
            )
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found" or e.response["error"] == "user_not_in_channel":
                self._slack_client.api_call(
                    "chat.postEphemeral",
                    channel=slack_user_identity.im_channel_id,
                    user=slack_user_identity.slack_id,
                    text=":white_check_mark: Alert successfully submitted",
                )
            else:
                raise e


class StartCreateIncidentFromSlashCommand(scenario_step.ScenarioStep):
    """
    StartCreateIncidentFromSlashCommand triggers creation of a manual incident from the slack message via slash command
    """

    command_name = [settings.SLACK_SLASH_COMMAND_NAME]
    TITLE_INPUT_BLOCK_ID = "TITLE_INPUT"
    MESSAGE_INPUT_BLOCK_ID = "MESSAGE_INPUT"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        input_id_prefix = _generate_input_id_prefix()

        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        private_metadata = {
            "channel_id": channel_id,
            "input_id_prefix": input_id_prefix,
            "with_title_and_message_inputs": True,
            "submit_routing_uid": FinishCreateIncidentFromSlashCommand.routing_uid(),
        }

        blocks = _get_manual_incident_initial_form_fields(
            slack_team_identity, slack_user_identity, input_id_prefix, payload, with_title_and_message_inputs=True
        )
        view = _get_manual_incident_form_view(
            FinishCreateIncidentFromSlashCommand.routing_uid(), blocks, json.dumps(private_metadata)
        )

        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class FinishCreateIncidentFromSlashCommand(scenario_step.ScenarioStep):
    """
    FinishCreateIncidentFromSlashCommand creates a manual incident from the slack message via slash message
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        Alert = apps.get_model("alerts", "Alert")

        title = _get_title_from_payload(payload)
        message = _get_message_from_payload(payload)

        private_metadata = json.loads(payload["view"]["private_metadata"])

        channel_id = private_metadata["channel_id"]

        input_id_prefix = private_metadata["input_id_prefix"]
        selected_organization = _get_selected_org_from_payload(payload, input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, input_id_prefix)
        selected_route = _get_selected_route_from_payload(payload, input_id_prefix)

        user = slack_user_identity.get_user(selected_organization)
        alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
            organization=selected_organization,
            team=selected_team,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={
                "author": user,
                "verbal_name": f"Manual incidents ({selected_team.name if selected_team else 'General'} team)",
            },
        )

        author_username = slack_user_identity.slack_verbal

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

        # Deprecated, use custom oncall property instead.
        # Update private metadata to use it in rendering:
        payload["view"]["private_metadata"] = private_metadata
        # Custom oncall property to simplify rendering
        payload["oncall"] = {}
        payload["oncall"]["title"] = title
        payload["oncall"]["message"] = message
        payload["oncall"]["author_username"] = author_username
        payload["oncall"]["permalink"] = None

        Alert.create(
            title=title,
            message=message,
            image_url=None,
            link_to_upstream_details=None,
            alert_receive_channel=alert_receive_channel,
            raw_request_data=payload,
            integration_unique_data={
                "created_by": author_username,
            },
            force_route_id=selected_route.pk,
        )


# OnChange steps responsible for rerendering manual incident creation form on change values in selects.
# They are works both with incident creation from submenu and slack command.


class OnOrgChange(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        private_metadata = json.loads(payload["view"]["private_metadata"])
        with_title_and_message_inputs = private_metadata.get("with_title_and_message_inputs", False)
        submit_routing_uid = private_metadata.get("submit_routing_uid")
        old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
            private_metadata
        )

        selected_organization = _get_selected_org_from_payload(payload, old_input_id_prefix)
        # Set selected team to default because org is changed.
        selected_team = None

        user = slack_user_identity.get_user(selected_organization)
        manual_integration = AlertReceiveChannel.get_or_create_manual_integration(
            organization=selected_organization,
            team=selected_team,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={
                "author": user,
                "verbal_name": f"Manual incidents ({selected_team.name if selected_team else 'General'} team)",
            },
        )
        selected_route = manual_integration.default_channel_filter

        organization_select = _get_organization_select(
            slack_team_identity, slack_user_identity, selected_organization, new_input_id_prefix
        )
        team_select = _get_team_select(slack_user_identity, selected_organization, selected_team, new_input_id_prefix)
        route_select = _get_route_select(manual_integration, selected_route, new_input_id_prefix)

        blocks = [organization_select, team_select, route_select]
        if with_title_and_message_inputs:
            blocks.extend([_get_title_input(payload), _get_message_input(payload)])
        view = _get_manual_incident_form_view(submit_routing_uid, blocks, json.dumps(new_private_metadata))
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnTeamChange(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        private_metadata = json.loads(payload["view"]["private_metadata"])
        with_title_and_message_inputs = private_metadata.get("with_title_and_message_inputs", False)
        submit_routing_uid = private_metadata.get("submit_routing_uid")
        old_input_id_prefix, new_input_id_prefix, new_private_metadata = _get_and_change_input_id_prefix_from_metadata(
            private_metadata
        )

        selected_organization = _get_selected_org_from_payload(payload, old_input_id_prefix)
        selected_team = _get_selected_team_from_payload(payload, old_input_id_prefix)

        user = slack_user_identity.get_user(selected_organization)
        manual_integration = AlertReceiveChannel.get_or_create_manual_integration(
            organization=selected_organization,
            team=selected_team,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={
                "author": user,
                "verbal_name": f"Manual incidents ({selected_team.name if selected_team else 'General'} team)",
            },
        )
        initial_route = manual_integration.default_channel_filter

        organization_select = _get_organization_select(
            slack_team_identity, slack_user_identity, selected_organization, new_input_id_prefix
        )
        team_select = _get_team_select(slack_user_identity, selected_organization, selected_team, new_input_id_prefix)
        route_select = _get_route_select(manual_integration, initial_route, new_input_id_prefix)

        blocks = [organization_select, team_select, route_select]
        if with_title_and_message_inputs:
            blocks.extend([_get_title_input(payload), _get_message_input(payload)])
        view = _get_manual_incident_form_view(submit_routing_uid, blocks, json.dumps(new_private_metadata))
        self._slack_client.api_call(
            "views.update",
            trigger_id=payload["trigger_id"],
            view=view,
            view_id=payload["view"]["id"],
        )


class OnRouteChange(scenario_step.ScenarioStep):
    """
    OnRouteChange is just a plug to handle change of value on route select
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        pass


def _get_manual_incident_form_view(routing_uid, blocks, private_metatada):
    view = {
        "type": "modal",
        "callback_id": routing_uid,
        "title": {
            "type": "plain_text",
            "text": "Start New Escalation",
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


def _get_manual_incident_initial_form_fields(
    slack_team_identity, slack_user_identity, input_id_prefix, payload, with_title_and_message_inputs=False
):
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
    team_select = _get_team_select(slack_user_identity, initial_organization, initial_team, input_id_prefix)

    user = slack_user_identity.get_user(initial_organization)
    manual_integration = AlertReceiveChannel.get_or_create_manual_integration(
        organization=initial_organization,
        team=initial_team,
        integration=AlertReceiveChannel.INTEGRATION_MANUAL,
        deleted_at=None,
        defaults={
            "author": user,
            "verbal_name": f"Manual incidents ({initial_team.name if initial_team else 'General'} team)",
        },
    )

    initial_route = manual_integration.default_channel_filter
    route_select = _get_route_select(manual_integration, initial_route, input_id_prefix)
    blocks = [organization_select, team_select, route_select]
    if with_title_and_message_inputs:
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
        "block_id": input_id_prefix + MANUAL_INCIDENT_ORG_SELECT_ID,
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
    selected_org_id = payload["view"]["state"]["values"][input_id_prefix + MANUAL_INCIDENT_ORG_SELECT_ID][
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
    for idx, team in enumerate(teams):
        if team == value:
            # Add 1 because default team option was added before cycle, so option indicies are shifted
            initial_option_idx = idx + 1
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
        "block_id": input_id_prefix + MANUAL_INCIDENT_TEAM_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select a team", "emoji": True},
            "options": team_options,
            "action_id": OnTeamChange.routing_uid(),
            "initial_option": team_options[initial_option_idx],
        },
    }
    return team_select


def _get_selected_team_from_payload(payload, input_id_prefix):
    Team = apps.get_model("user_management", "Team")
    selected_team_id = payload["view"]["state"]["values"][input_id_prefix + MANUAL_INCIDENT_TEAM_SELECT_ID][
        OnTeamChange.routing_uid()
    ]["selected_option"]["value"]
    if selected_team_id == DEFAULT_TEAM_VALUE:
        return None
    team = Team.objects.filter(pk=selected_team_id).first()
    return team


def _get_route_select(integration, value, input_id_prefix):
    route_options = []
    initial_option_idx = 0
    for idx, route in enumerate(integration.channel_filters.all()):
        filtering_term = f'"{route.filtering_term}"'
        if route.is_default:
            filtering_term = "default"
        if value == route:
            initial_option_idx = idx
        route_options.append(
            {
                "text": {
                    "type": "plain_text",
                    "text": f"{filtering_term}",
                    "emoji": True,
                },
                "value": f"{route.pk}",
            }
        )
    route_select = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Select a route"},
        "block_id": input_id_prefix + MANUAL_INCIDENT_ROUTE_SELECT_ID,
        "accessory": {
            "type": "static_select",
            "placeholder": {"type": "plain_text", "text": "Select a route", "emoji": True},
            "options": route_options,
            "initial_option": route_options[initial_option_idx],
            "action_id": OnRouteChange.routing_uid(),
        },
    }
    return route_select


def _get_selected_route_from_payload(payload, input_id_prefix):
    ChannelFilter = apps.get_model("alerts", "ChannelFilter")
    selected_org_id = payload["view"]["state"]["values"][input_id_prefix + MANUAL_INCIDENT_ROUTE_SELECT_ID][
        OnRouteChange.routing_uid()
    ]["selected_option"]["value"]
    channel_filter = ChannelFilter.objects.filter(pk=selected_org_id).first()
    return channel_filter


def _get_and_change_input_id_prefix_from_metadata(metadata):
    old_input_id_prefix = metadata["input_id_prefix"]
    new_input_id_prefix = _generate_input_id_prefix()
    metadata["input_id_prefix"] = new_input_id_prefix
    return old_input_id_prefix, new_input_id_prefix, metadata


def _get_title_input(payload):
    title_input_block = {
        "type": "input",
        "block_id": MANUAL_INCIDENT_TITLE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Title:",
        },
        "element": {
            "type": "plain_text_input",
            "action_id": FinishCreateIncidentFromSlashCommand.routing_uid(),
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
    title = payload["view"]["state"]["values"][MANUAL_INCIDENT_TITLE_INPUT_ID][
        FinishCreateIncidentFromSlashCommand.routing_uid()
    ]["value"]
    return title


def _get_message_input(payload):
    message_input_block = {
        "type": "input",
        "block_id": MANUAL_INCIDENT_MESSAGE_INPUT_ID,
        "label": {
            "type": "plain_text",
            "text": "Message:",
        },
        "element": {
            "type": "plain_text_input",
            "action_id": FinishCreateIncidentFromSlashCommand.routing_uid(),
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
        payload["view"]["state"]["values"][MANUAL_INCIDENT_MESSAGE_INPUT_ID][
            FinishCreateIncidentFromSlashCommand.routing_uid()
        ]["value"]
        or ""
    )
    return message


# _generate_input_id_prefix returns uniq str to not to preserve input's values between view update
#  https://api.slack.com/methods/views.update#markdown
def _generate_input_id_prefix():
    return str(uuid4())


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_MESSAGE_ACTION,
        "message_action_callback_id": StartCreateIncidentFromMessage.callback_id,
        "step": StartCreateIncidentFromMessage,
    },
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
        "block_action_id": OnRouteChange.routing_uid(),
        "step": OnRouteChange,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": FinishCreateIncidentFromMessage.routing_uid(),
        "step": FinishCreateIncidentFromMessage,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_SLASH_COMMAND,
        "command_name": StartCreateIncidentFromSlashCommand.command_name,
        "step": StartCreateIncidentFromSlashCommand,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": FinishCreateIncidentFromSlashCommand.routing_uid(),
        "step": FinishCreateIncidentFromSlashCommand,
    },
]
