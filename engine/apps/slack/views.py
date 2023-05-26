import hashlib
import hmac
import json
import logging
from typing import Optional

from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings
from apps.slack.scenarios.alertgroup_appearance import STEPS_ROUTING as ALERTGROUP_APPEARANCE_ROUTING

# Importing routes from scenarios
from apps.slack.scenarios.declare_incident import STEPS_ROUTING as DECLARE_INCIDENT_ROUTING
from apps.slack.scenarios.distribute_alerts import STEPS_ROUTING as DISTRIBUTION_STEPS_ROUTING
from apps.slack.scenarios.invited_to_channel import STEPS_ROUTING as INVITED_TO_CHANNEL_ROUTING
from apps.slack.scenarios.manual_incident import STEPS_ROUTING as MANUAL_INCIDENT_ROUTING
from apps.slack.scenarios.notified_user_not_in_channel import STEPS_ROUTING as NOTIFIED_USER_NOT_IN_CHANNEL_ROUTING
from apps.slack.scenarios.onboarding import STEPS_ROUTING as ONBOARDING_STEPS_ROUTING
from apps.slack.scenarios.paging import STEPS_ROUTING as DIRECT_PAGE_ROUTING
from apps.slack.scenarios.profile_update import STEPS_ROUTING as PROFILE_UPDATE_ROUTING
from apps.slack.scenarios.resolution_note import STEPS_ROUTING as RESOLUTION_NOTE_ROUTING
from apps.slack.scenarios.scenario_step import (
    EVENT_SUBTYPE_BOT_MESSAGE,
    EVENT_SUBTYPE_FILE_SHARE,
    EVENT_SUBTYPE_MESSAGE_CHANGED,
    EVENT_SUBTYPE_MESSAGE_DELETED,
    EVENT_TYPE_APP_MENTION,
    EVENT_TYPE_MESSAGE,
    EVENT_TYPE_MESSAGE_CHANNEL,
    EVENT_TYPE_SUBTEAM_CREATED,
    EVENT_TYPE_SUBTEAM_MEMBERS_CHANGED,
    EVENT_TYPE_SUBTEAM_UPDATED,
    EVENT_TYPE_USER_CHANGE,
    EVENT_TYPE_USER_PROFILE_CHANGED,
    PAYLOAD_TYPE_BLOCK_ACTIONS,
    PAYLOAD_TYPE_DIALOG_SUBMISSION,
    PAYLOAD_TYPE_EVENT_CALLBACK,
    PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
    PAYLOAD_TYPE_MESSAGE_ACTION,
    PAYLOAD_TYPE_SLASH_COMMAND,
    PAYLOAD_TYPE_VIEW_SUBMISSION,
    ScenarioStep,
)
from apps.slack.scenarios.schedules import STEPS_ROUTING as SCHEDULES_ROUTING
from apps.slack.scenarios.slack_channel import STEPS_ROUTING as CHANNEL_ROUTING
from apps.slack.scenarios.slack_channel_integration import STEPS_ROUTING as SLACK_CHANNEL_INTEGRATION_ROUTING
from apps.slack.scenarios.slack_usergroup import STEPS_ROUTING as SLACK_USERGROUP_UPDATE_ROUTING
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from apps.slack.tasks import clean_slack_integration_leftovers, unpopulate_slack_user_identities
from apps.user_management.models import Organization
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log
from common.oncall_gateway import delete_slack_connector

from .models import SlackMessage, SlackTeamIdentity, SlackUserIdentity

SCENARIOS_ROUTES = []  # Add all other routes here
SCENARIOS_ROUTES.extend(ONBOARDING_STEPS_ROUTING)
SCENARIOS_ROUTES.extend(DISTRIBUTION_STEPS_ROUTING)
SCENARIOS_ROUTES.extend(INVITED_TO_CHANNEL_ROUTING)
SCENARIOS_ROUTES.extend(SCHEDULES_ROUTING)
SCENARIOS_ROUTES.extend(SLACK_CHANNEL_INTEGRATION_ROUTING)
SCENARIOS_ROUTES.extend(ALERTGROUP_APPEARANCE_ROUTING)
SCENARIOS_ROUTES.extend(RESOLUTION_NOTE_ROUTING)
SCENARIOS_ROUTES.extend(SLACK_USERGROUP_UPDATE_ROUTING)
SCENARIOS_ROUTES.extend(CHANNEL_ROUTING)
SCENARIOS_ROUTES.extend(PROFILE_UPDATE_ROUTING)
SCENARIOS_ROUTES.extend(MANUAL_INCIDENT_ROUTING)
SCENARIOS_ROUTES.extend(DIRECT_PAGE_ROUTING)
SCENARIOS_ROUTES.extend(DECLARE_INCIDENT_ROUTING)
SCENARIOS_ROUTES.extend(NOTIFIED_USER_NOT_IN_CHANNEL_ROUTING)

logger = logging.getLogger(__name__)

SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID = "SELECT_ORGANIZATION_AND_ROUTE"


class StopAnalyticsReporting(APIView):
    def get(self, request):
        response = HttpResponse(
            "Your app installation would not be tracked by analytics from backend, "
            "use browser plugin to disable from a frontend side. "
        )
        response.set_cookie("no_track", True, max_age=10 * 360 * 24 * 60 * 60)
        return response


class InstallLinkRedirectView(APIView):
    def get(self, request, subscription="free", utm="not_specified"):
        return HttpResponse(("Sign up is not allowed"), status=status.HTTP_400_BAD_REQUEST)


class SignupRedirectView(APIView):
    def get(self, request, subscription="free", utm="not_specified"):
        return HttpResponse(("Sign up is not allowed"), status=status.HTTP_400_BAD_REQUEST)


class OAuthSlackView(APIView):
    def get(self, request, format=None, subscription="free", utm="not_specified"):
        return HttpResponse(("Sign up is not allowed"), status=status.HTTP_400_BAD_REQUEST)


class SlackEventApiEndpointView(APIView):
    @staticmethod
    def verify_signature(timestamp, signature, body, secret):
        # https://github.com/slackapi/python-slack-events-api/blob/master/slackeventsapi/server.py#L47

        if hasattr(hmac, "compare_digest"):
            req = str.encode("v0:" + str(timestamp) + ":") + body
            request_hash = "v0=" + hmac.new(str.encode(secret), req, hashlib.sha256).hexdigest()
            return hmac.compare_digest(request_hash, signature)

    def get(self, request, format=None):
        return Response("hello")

    def post(self, request):
        logger.info("Request id: {}".format(request.META.get("HTTP_X_REQUEST_ID")))
        body = request.body

        try:
            slack_signature = request.META["HTTP_X_SLACK_SIGNATURE"]
            slack_request_timestamp = request.META["HTTP_X_SLACK_REQUEST_TIMESTAMP"]
        except KeyError:
            logger.warning("X-Slack-Signature or X-Slack-Request_Timestamp don't exist, This request is not from slack")
            return Response(status=403)

        if not settings.DEBUG:
            if live_settings.SLACK_SIGNING_SECRET is None and settings.SLACK_SIGNING_SECRET_LIVE:
                raise Exception("Please specify SLACK_SIGNING_SECRET or use DEBUG.")

            if not (
                SlackEventApiEndpointView.verify_signature(
                    slack_request_timestamp, slack_signature, body, live_settings.SLACK_SIGNING_SECRET
                )
                or SlackEventApiEndpointView.verify_signature(
                    slack_request_timestamp, slack_signature, body, settings.SLACK_SIGNING_SECRET_LIVE
                )
            ):
                return Response(status=403)

        # Unifying payload
        if "payload" in request.data:
            payload = request.data["payload"]
        else:
            payload = request.data
        if isinstance(payload, str):
            payload = json.JSONDecoder().decode(payload)

        logger.debug(f"Slack payload is {payload}")

        # Checking if it's repeated Slack request
        if "HTTP_X_SLACK_RETRY_NUM" in request.META and int(request.META["HTTP_X_SLACK_RETRY_NUM"]) > 1:
            logger.critical(
                "Slack retries {} time, request data: {}".format(request.META["HTTP_X_SLACK_RETRY_NUM"], request.data)
            )
            payload["amixr_slack_retries"] = request.META["HTTP_X_SLACK_RETRY_NUM"]

        # Initial url verification
        if "type" in payload and payload["type"] == "url_verification":
            logger.critical("URL verification from Slack side. That's suspicious.")
            return Response(payload["challenge"])

        # Linking team
        slack_team_identity = self._get_slack_team_identity_from_payload(payload)

        if not slack_team_identity:
            logger.info("Dropping request because it does not have SlackTeamIdentity.")
            return Response()

        # Means that slack_team_identity unpopulated
        if not slack_team_identity.organizations.exists():
            logger.warning(f"OnCall Team for SlackTeamIdentity is not detected, stop it!")
            # Open pop-up to inform user why OnCall bot doesn't work if any action was triggered
            warning_text = (
                "OnCall is not able to process this action because this Slack workspace was "
                "disconnected from OnCall. Please log in to the OnCall web interface and install "
                "Slack Integration with this workspace again."
            )
            self._open_warning_window_if_needed(payload, slack_team_identity, warning_text)
            return Response(status=200)

        # Todo: the case when team has no keys is unexpected, investigation is required
        if slack_team_identity.access_token is None and slack_team_identity.bot_access_token is None:
            logger.info(f"Team {slack_team_identity.slack_id} has no keys, dropping request.")
            return Response()

        sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)

        if slack_team_identity.detected_token_revoked is not None:
            # check if token is still invalid
            try:
                sc.api_call(
                    "auth.test",
                    team=slack_team_identity,
                )
            except SlackAPITokenException:
                logger.info(f"Team {slack_team_identity.slack_id} has revoked token, dropping request.")
                return Response(status=200)

        Step = None
        step_was_found = False

        slack_user_id = None
        user = None
        # Linking user identity
        slack_user_identity = None

        if "event" in payload and payload["event"] is not None:
            if ("user" in payload["event"]) and slack_team_identity and (payload["event"]["user"] is not None):
                if "id" in payload["event"]["user"]:
                    slack_user_id = payload["event"]["user"]["id"]
                elif type(payload["event"]["user"]) is str:
                    slack_user_id = payload["event"]["user"]
                else:
                    raise Exception("Failed Linking user identity")

            elif (
                ("bot_id" in payload["event"])
                and slack_team_identity
                and (
                    payload["event"]["bot_id"] is not None
                    and "channel_type" in payload["event"]
                    and payload["event"]["channel_type"] == EVENT_TYPE_MESSAGE_CHANNEL
                )
            ):
                response = sc.api_call("bots.info", bot=payload["event"]["bot_id"])
                bot_user_id = response.get("bot", {}).get("user_id", "")

                # Don't react on own bot's messages.
                if bot_user_id == slack_team_identity.bot_user_id:
                    return Response(status=200)

            elif "user" in payload["event"].get("message", {}):
                slack_user_id = payload["event"]["message"]["user"]
            # event subtype 'message_deleted'
            elif "user" in payload["event"].get("previous_message", {}):
                slack_user_id = payload["event"]["previous_message"]["user"]

        if "user" in payload:
            slack_user_id = payload["user"]["id"]

        elif "user_id" in payload:
            slack_user_id = payload["user_id"]

        if slack_user_id is not None and slack_user_id != slack_team_identity.bot_user_id:
            slack_user_identity = SlackUserIdentity.objects.filter(
                slack_id=slack_user_id,
                slack_team_identity=slack_team_identity,
            ).first()

        organization = self._get_organization_from_payload(payload, slack_team_identity)
        logger.info("Organization: " + str(organization))
        logger.info("SlackUserIdentity detected: " + str(slack_user_identity))

        if not slack_user_identity:
            if "type" in payload and payload["type"] == PAYLOAD_TYPE_EVENT_CALLBACK:
                if payload["event"]["type"] in [
                    EVENT_TYPE_SUBTEAM_CREATED,
                    EVENT_TYPE_SUBTEAM_UPDATED,
                    EVENT_TYPE_SUBTEAM_MEMBERS_CHANGED,
                ]:
                    logger.info("Slack event without user slack_id.")
                elif payload["event"]["type"] in (EVENT_TYPE_USER_CHANGE, EVENT_TYPE_USER_PROFILE_CHANGED):
                    logger.info(
                        "Event {}. Dropping request because it does not have SlackUserIdentity.".format(
                            payload["event"]["type"]
                        )
                    )
                    return Response()
            else:
                logger.info("Dropping request because it does not have SlackUserIdentity.")
                self._open_warning_for_unconnected_user(sc, payload)
                return Response()
        elif organization:
            user = slack_user_identity.get_user(organization)
            if not user:
                # Means that user slack_user_identity is not in any organization, connected to this Slack workspace
                warning_text = "Permission denied. Please connect your Slack account to OnCall."
                # Open pop-up to inform user why OnCall bot doesn't work if any action was triggered
                self._open_warning_window_if_needed(payload, slack_team_identity, warning_text)
                return Response(status=200)
        elif organization is None:
            # see this GitHub issue for more context on how this situation can arise
            # https://github.com/grafana/oncall-private/issues/1836
            # tldr; > 2 stacks, stack A and stack B, use the same Slack workspace. Stack A get deleted
            # the
            warning_text = (
                "OnCall is not able to process this action because one of the following scenarios: \n"
                "1. The Slack chatops integration was disconnected from the instance that the Alert Group belongs "
                "to, BUT the Slack workspace is still connected to another instance as well. In this case, simply log "
                "in to the OnCall web interface and re-install the Slack Integration with this workspace again.\n"
                "2. (Less likely) The Grafana instance belonging to this Alert Group was delete. In this case the Alert Group is orphaned and cannot be acted upon."
            )
            # Open pop-up to inform user why OnCall bot doesn't work if any action was triggered
            self._open_warning_window_if_needed(payload, slack_team_identity, warning_text)
            return Response(status=200)
        elif not slack_user_identity.users.exists():
            # Means that slack_user_identity doesn't have any connected user
            # Open pop-up to inform user why OnCall bot doesn't work if any action was triggered
            self._open_warning_for_unconnected_user(sc, payload)
            return Response(status=200)

        # Capture cases when we expect stateful message from user
        if not step_was_found and "type" in payload and payload["type"] == PAYLOAD_TYPE_EVENT_CALLBACK:
            # Message event is from channel
            if (
                payload["event"]["type"] == EVENT_TYPE_MESSAGE
                and payload["event"]["channel_type"] == EVENT_TYPE_MESSAGE_CHANNEL
                and (
                    "subtype" not in payload["event"]
                    or payload["event"]["subtype"] == EVENT_SUBTYPE_BOT_MESSAGE
                    or payload["event"]["subtype"] == EVENT_SUBTYPE_MESSAGE_CHANGED
                    or payload["event"]["subtype"] == EVENT_SUBTYPE_FILE_SHARE
                    or payload["event"]["subtype"] == EVENT_SUBTYPE_MESSAGE_DELETED
                )
            ):
                for route in SCENARIOS_ROUTES:
                    if (
                        "message_channel_type" in route
                        and payload["event"]["channel_type"] == route["message_channel_type"]
                    ):
                        Step = route["step"]
                        logger.info("Routing to {}".format(Step))
                        step = Step(slack_team_identity, organization, user)
                        step.process_scenario(slack_user_identity, slack_team_identity, payload)
                        step_was_found = True
            # We don't do anything on app mention, but we doesn't want to unsubscribe from this event yet.
            if payload["event"]["type"] == EVENT_TYPE_APP_MENTION:
                logger.info(f"Received event of type {EVENT_TYPE_APP_MENTION} from slack. Skipping.")
                return Response(status=200)
        # Routing to Steps based on routing rules
        if not step_was_found:
            for route in SCENARIOS_ROUTES:
                # Slash commands have to "type"
                if "command" in payload and route["payload_type"] == PAYLOAD_TYPE_SLASH_COMMAND:
                    if payload["command"] in route["command_name"]:
                        Step = route["step"]
                        logger.info("Routing to {}".format(Step))
                        step = Step(slack_team_identity, organization, user)
                        step.process_scenario(slack_user_identity, slack_team_identity, payload)
                        step_was_found = True

                if "type" in payload and payload["type"] == route["payload_type"]:
                    if payload["type"] == PAYLOAD_TYPE_EVENT_CALLBACK:
                        if payload["event"]["type"] == route["event_type"]:
                            # event_name is used for stateful
                            if "event_name" not in route:
                                Step = route["step"]
                                logger.info("Routing to {}".format(Step))
                                step = Step(slack_team_identity, organization, user)
                                step.process_scenario(slack_user_identity, slack_team_identity, payload)
                                step_was_found = True

                    if payload["type"] == PAYLOAD_TYPE_INTERACTIVE_MESSAGE:
                        for action in payload["actions"]:
                            if action["type"] == route["action_type"]:
                                # Action name may also contain action arguments.
                                # So only beginning is used for routing.
                                if action["name"].startswith(route["action_name"]):
                                    Step = route["step"]
                                    logger.info("Routing to {}".format(Step))
                                    step = Step(slack_team_identity, organization, user)
                                    result = step.process_scenario(slack_user_identity, slack_team_identity, payload)
                                    if result is not None:
                                        return result
                                    step_was_found = True

                    if payload["type"] == PAYLOAD_TYPE_BLOCK_ACTIONS:
                        for action in payload["actions"]:
                            if action["type"] == route["block_action_type"]:
                                if action["action_id"].startswith(route["block_action_id"]):
                                    Step = route["step"]
                                    logger.info("Routing to {}".format(Step))
                                    step = Step(slack_team_identity, organization, user)
                                    step.process_scenario(slack_user_identity, slack_team_identity, payload)
                                    step_was_found = True

                    if payload["type"] == PAYLOAD_TYPE_DIALOG_SUBMISSION:
                        if payload["callback_id"] == route["dialog_callback_id"]:
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            result = step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            if result is not None:
                                return result
                            step_was_found = True

                    if payload["type"] == PAYLOAD_TYPE_VIEW_SUBMISSION:
                        if payload["view"]["callback_id"].startswith(route["view_callback_id"]):
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            result = step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            if result is not None:
                                return result
                            step_was_found = True

                    if payload["type"] == PAYLOAD_TYPE_MESSAGE_ACTION:
                        if payload["callback_id"] in route["message_action_callback_id"]:
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            step_was_found = True

        if not step_was_found:
            raise Exception("Step is undefined" + str(payload))

        return Response(status=200)

    def _get_slack_team_identity_from_payload(self, payload) -> Optional[SlackTeamIdentity]:
        slack_team_identity = None

        if "team" in payload:
            slack_team_id = payload["team"]["id"]
        elif "team_id" in payload:
            slack_team_id = payload["team_id"]
        else:
            return slack_team_identity

        try:
            slack_team_identity = SlackTeamIdentity.objects.get(slack_id=slack_team_id)
        except SlackTeamIdentity.DoesNotExist as e:
            logger.warning("Team identity not detected, that's dangerous!" + str(e))
        return slack_team_identity

    def _get_organization_from_payload(self, payload, slack_team_identity):
        message_ts = None
        channel_id = None
        organization = None

        try:
            # view submission or actions in view
            if "view" in payload:
                organization_id = None
                private_metadata = payload["view"].get("private_metadata")
                # steps with private_metadata in which we know organization before open view
                if private_metadata and "organization_id" in private_metadata:
                    organization_id = json.loads(private_metadata).get("organization_id")
                # steps with organization selection in view (e.g. slash commands)
                elif SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID in payload["view"].get("state", {}).get("values", {}):
                    payload_values = payload["view"]["state"]["values"]
                    selected_value = payload_values[SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID][
                        SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID
                    ]["selected_option"]["value"]
                    organization_id = int(selected_value.split("-")[0])
                if organization_id:
                    organization = slack_team_identity.organizations.get(pk=organization_id)
                    return organization
            # buttons and actions
            elif payload.get("type") in [
                PAYLOAD_TYPE_BLOCK_ACTIONS,
                PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
                PAYLOAD_TYPE_MESSAGE_ACTION,
            ]:
                # for cases when we put organization_id into action value (e.g. public suggestion)
                if (
                    payload.get("actions")
                    and payload["actions"][0].get("value", {})
                    and "organization_id" in payload["actions"][0]["value"]
                ):
                    organization_id = int(json.loads(payload["actions"][0]["value"])["organization_id"])
                    organization = slack_team_identity.organizations.get(pk=organization_id)
                    return organization

                channel_id = payload["channel"]["id"]
                if "message" in payload:
                    message_ts = payload["message"].get("thread_ts") or payload["message"]["ts"]
                # for interactive message
                elif "message_ts" in payload:
                    message_ts = payload["message_ts"]
                else:
                    return
            # events
            elif payload.get("type") == PAYLOAD_TYPE_EVENT_CALLBACK:
                if "channel" in payload["event"]:  # events without channel: user_change, events with subteam, etc.
                    channel_id = payload["event"]["channel"]

                if "message" in payload["event"]:
                    message_ts = payload["event"]["message"].get("thread_ts") or payload["event"]["message"]["ts"]
                elif "thread_ts" in payload["event"]:
                    message_ts = payload["event"]["thread_ts"]
                else:
                    return

            if not (message_ts and channel_id):
                return

            try:
                slack_message = SlackMessage.objects.get(
                    slack_id=message_ts,
                    _slack_team_identity=slack_team_identity,
                    channel_id=channel_id,
                )
            except SlackMessage.DoesNotExist:
                pass
            else:
                alert_group = slack_message.get_alert_group()
                if alert_group:
                    organization = alert_group.channel.organization
                    return organization
            return organization
        except Organization.DoesNotExist:
            # see this GitHub issue for more context on how this situation can arise
            # https://github.com/grafana/oncall-private/issues/1836
            return None

    def _open_warning_window_if_needed(self, payload, slack_team_identity, warning_text) -> None:
        if payload.get("trigger_id") is not None:
            step = ScenarioStep(slack_team_identity)
            try:
                step.open_warning_window(payload, warning_text)
            except SlackAPIException as e:
                logger.info(
                    f"Failed to open pop-up for unpopulated SlackTeamIdentity {slack_team_identity.pk}\n" f"Error: {e}"
                )

    def _open_warning_for_unconnected_user(self, slack_client, payload):
        if payload.get("trigger_id") is None:
            return

        text = (
            "The information in this workspace is read-only. To interact with OnCall alert groups you need to connect a personal account.\n"
            "Please go to *Grafana* -> *OnCall* -> *Users*, "
            "choose *your profile* and click the *connect* button.\n"
            ":rocket: :rocket: :rocket:"
        )

        view = {
            "blocks": (
                {"type": "section", "block_id": "section-identifier", "text": {"type": "mrkdwn", "text": text}},
            ),
            "type": "modal",
            "callback_id": "modal-identifier",
            "title": {
                "type": "plain_text",
                "text": "One more step!",
            },
        }
        slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class ResetSlackView(APIView):

    permission_classes = (IsAuthenticated, RBACPermission)
    authentication_classes = [PluginAuthentication]

    rbac_permissions = {
        "post": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    def post(self, request):
        if settings.SLACK_INTEGRATION_MAINTENANCE_ENABLED:
            response = Response(
                "Grafana OnCall is temporary unable to connect your slack account or install OnCall to your slack workspace",
                status=400,
            )
        else:
            organization = request.auth.organization
            slack_team_identity = organization.slack_team_identity
            if slack_team_identity is not None:
                clean_slack_integration_leftovers.apply_async((organization.pk,))
                if settings.FEATURE_MULTIREGION_ENABLED:
                    delete_slack_connector(str(organization.uuid))
                write_chatops_insight_log(
                    author=request.user,
                    event_name=ChatOpsEvent.WORKSPACE_DISCONNECTED,
                    chatops_type=ChatOpsTypePlug.SLACK.value,
                )
                unpopulate_slack_user_identities(organization.pk, True)
                response = Response(status=200)
            else:
                response = Response(status=400)
        return response
