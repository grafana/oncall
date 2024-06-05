import hashlib
import hmac
import json
import logging
from contextlib import suppress

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings
from apps.slack.client import SlackClient
from apps.slack.errors import SlackAPIError
from apps.slack.scenarios.alertgroup_appearance import STEPS_ROUTING as ALERTGROUP_APPEARANCE_ROUTING

# Importing routes from scenarios
from apps.slack.scenarios.declare_incident import STEPS_ROUTING as DECLARE_INCIDENT_ROUTING
from apps.slack.scenarios.distribute_alerts import STEPS_ROUTING as DISTRIBUTION_STEPS_ROUTING
from apps.slack.scenarios.invited_to_channel import STEPS_ROUTING as INVITED_TO_CHANNEL_ROUTING
from apps.slack.scenarios.manage_responders import STEPS_ROUTING as MANAGE_RESPONDERS_ROUTING
from apps.slack.scenarios.notified_user_not_in_channel import STEPS_ROUTING as NOTIFIED_USER_NOT_IN_CHANNEL_ROUTING
from apps.slack.scenarios.onboarding import STEPS_ROUTING as ONBOARDING_STEPS_ROUTING
from apps.slack.scenarios.paging import STEPS_ROUTING as DIRECT_PAGE_ROUTING
from apps.slack.scenarios.profile_update import STEPS_ROUTING as PROFILE_UPDATE_ROUTING
from apps.slack.scenarios.resolution_note import STEPS_ROUTING as RESOLUTION_NOTE_ROUTING
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.scenarios.schedules import STEPS_ROUTING as SCHEDULES_ROUTING
from apps.slack.scenarios.shift_swap_requests import STEPS_ROUTING as SHIFT_SWAP_REQUESTS_ROUTING
from apps.slack.scenarios.slack_channel import STEPS_ROUTING as CHANNEL_ROUTING
from apps.slack.scenarios.slack_channel_integration import STEPS_ROUTING as SLACK_CHANNEL_INTEGRATION_ROUTING
from apps.slack.scenarios.slack_usergroup import STEPS_ROUTING as SLACK_USERGROUP_UPDATE_ROUTING
from apps.slack.types import EventPayload, EventType, MessageEventSubtype, PayloadType, ScenarioRoute
from apps.user_management.models import Organization

from .errors import SlackAPITokenError
from .installation import SlackInstallationExc, uninstall_slack_integration
from .models import SlackMessage, SlackTeamIdentity, SlackUserIdentity
from .slash_command import SlashCommand

SCENARIOS_ROUTES: ScenarioRoute.RoutingSteps = []
SCENARIOS_ROUTES.extend(ONBOARDING_STEPS_ROUTING)
SCENARIOS_ROUTES.extend(DISTRIBUTION_STEPS_ROUTING)
SCENARIOS_ROUTES.extend(INVITED_TO_CHANNEL_ROUTING)
SCENARIOS_ROUTES.extend(SCHEDULES_ROUTING)
SCENARIOS_ROUTES.extend(SHIFT_SWAP_REQUESTS_ROUTING)
SCENARIOS_ROUTES.extend(SLACK_CHANNEL_INTEGRATION_ROUTING)
SCENARIOS_ROUTES.extend(ALERTGROUP_APPEARANCE_ROUTING)
SCENARIOS_ROUTES.extend(RESOLUTION_NOTE_ROUTING)
SCENARIOS_ROUTES.extend(SLACK_USERGROUP_UPDATE_ROUTING)
SCENARIOS_ROUTES.extend(CHANNEL_ROUTING)
SCENARIOS_ROUTES.extend(PROFILE_UPDATE_ROUTING)
SCENARIOS_ROUTES.extend(DIRECT_PAGE_ROUTING)
SCENARIOS_ROUTES.extend(MANAGE_RESPONDERS_ROUTING)
SCENARIOS_ROUTES.extend(DECLARE_INCIDENT_ROUTING)
SCENARIOS_ROUTES.extend(NOTIFIED_USER_NOT_IN_CHANNEL_ROUTING)

logger = logging.getLogger(__name__)


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

        logger.info(f"Slack payload is {payload}")

        # Checking if it's repeated Slack request
        if "HTTP_X_SLACK_RETRY_NUM" in request.META and int(request.META["HTTP_X_SLACK_RETRY_NUM"]) > 1:
            logger.critical(
                "Slack retries {} time, request data: {}".format(request.META["HTTP_X_SLACK_RETRY_NUM"], request.data)
            )
            payload["amixr_slack_retries"] = request.META["HTTP_X_SLACK_RETRY_NUM"]

        payload_type = payload.get("type")
        payload_type_is_block_actions = payload_type == PayloadType.BLOCK_ACTIONS
        payload_command = payload.get("command")
        payload_callback_id = payload.get("callback_id")
        payload_actions = payload.get("actions", [])
        payload_user = payload.get("user")
        payload_user_id = payload.get("user_id")

        edit_schedule_actions = {s["block_action_id"] for s in SCHEDULES_ROUTING}
        payload_action_edit_schedule = (
            payload_actions[0].get("action_id") in edit_schedule_actions if payload_actions else False
        )

        payload_event = payload.get("event", {})
        payload_event_type = payload_event.get("type")
        payload_event_subtype = payload_event.get("subtype")
        payload_event_user = payload_event.get("user")
        payload_event_bot_id = payload_event.get("bot_id")
        payload_event_channel_type = payload_event.get("channel_type")

        payload_event_message = payload_event.get("message", {})
        payload_event_message_user = payload_event_message.get("user")

        payload_event_previous_message = payload_event.get("previous_message", {})
        payload_event_previous_message_user = payload_event_previous_message.get("user")

        # Initial url verification
        if payload_type == "url_verification":
            logger.critical("URL verification from Slack side. That's suspicious.")
            return Response(payload["challenge"])

        # Linking team
        slack_team_identity = self._get_slack_team_identity_from_payload(payload)

        if not slack_team_identity:
            logger.info("Dropping request because it does not have SlackTeamIdentity.")
            return Response()

        # Means that slack_team_identity unpopulated
        if not slack_team_identity.organizations.exists():
            logger.warning("OnCall Team for SlackTeamIdentity is not detected, stop it!")
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

        sc = SlackClient(slack_team_identity)

        if slack_team_identity.detected_token_revoked:
            try:
                sc.auth_test()  # check if token is still invalid
            except SlackAPITokenError:
                return Response(status=200)

        Step = None
        step_was_found = False

        slack_user_id = None
        user = None
        # Linking user identity
        slack_user_identity = None

        if payload_event:
            if payload_event_user and slack_team_identity:
                if payload_event_bot_id and payload_event_bot_id == slack_team_identity.bot_id:
                    """
                    messages from slack apps have both user and bot_id in the payload:
                    {...
                        "bot_id":"BSVC95WJZ",
                        "type":"message",
                        "text":"HELLO",
                        "user":"USX7UADC7",
                        "ts":"1701082318.471149",
                        "app_id":"ASUTJU5U4",
                    ...}
                    So check bot_id even if payload has a user to not to react on own bot messages.
                    """
                    return Response(status=200)

                if "id" in payload_event_user:
                    slack_user_id = payload_event_user["id"]
                elif type(payload_event_user) is str:
                    slack_user_id = payload_event_user
                else:
                    raise Exception("Failed Linking user identity")

            elif (
                payload_event_bot_id and slack_team_identity and payload_event_channel_type == EventType.MESSAGE_CHANNEL
            ):
                """
                Another case of incoming messages from bots. These payloads has only bot_id, but no user field:
                {..
                    "type":"message",
                    "subtype":"bot_message",
                    "text":"",
                    "ts":"1701143460.869349",
                    "username":"some_bot_username",
                ...}

                It looks like it's a payload from legacy slack "Incoming Webhooks" integration
                https://raintank-corp.slack.com/apps/A0F7XDUAZ-incoming-webhooks?tab=more_info
                """
                # Don't react on own bot's messages.
                if payload_event_bot_id == slack_team_identity.bot_id:
                    return Response(status=200)
            elif payload_event_message_user:
                slack_user_id = payload_event_message_user
            # event subtype 'message_deleted'
            elif payload_event_previous_message_user:
                slack_user_id = payload_event_previous_message_user

        if payload_user:
            slack_user_id = payload_user["id"]

        elif payload_user_id:
            slack_user_id = payload_user_id

        if slack_user_id is not None and slack_user_id != slack_team_identity.bot_user_id:
            slack_user_identity = SlackUserIdentity.objects.filter(
                slack_id=slack_user_id,
                slack_team_identity=slack_team_identity,
            ).first()

        organization = self._get_organization_from_payload(payload, slack_team_identity)
        logger.info("Organization: " + str(organization))
        logger.info("SlackUserIdentity detected: " + str(slack_user_identity))

        if not slack_user_identity:
            if payload_type == PayloadType.EVENT_CALLBACK:
                if payload_event_type in [
                    EventType.SUBTEAM_CREATED,
                    EventType.SUBTEAM_UPDATED,
                    EventType.SUBTEAM_MEMBERS_CHANGED,
                ]:
                    logger.info("Slack event without user slack_id.")
                elif payload_event_type in (EventType.USER_CHANGE, EventType.USER_PROFILE_CHANGED):
                    logger.info(
                        f"Event {payload_event_type}. Dropping request because it does not have SlackUserIdentity."
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
        # direct paging / manual incident / schedule update dialogs don't require organization to be set
        elif (
            organization is None
            and payload_type_is_block_actions
            and not (payload.get("view") or payload_action_edit_schedule)
        ):
            # see this GitHub issue for more context on how this situation can arise
            # https://github.com/grafana/oncall-private/issues/1836
            warning_text = (
                "OnCall is not able to process this action because one of the following scenarios: \n"
                "1. The Slack chatops integration was disconnected from the instance that the Alert Group belongs "
                "to, BUT the Slack workspace is still connected to another instance as well. In this case, simply log "
                "in to the OnCall web interface and re-install the Slack Integration with this workspace again.\n"
                "2. (Less likely) The Grafana instance belonging to this Alert Group was deleted. In this case the Alert Group is orphaned and cannot be acted upon."
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
        if payload_type == PayloadType.EVENT_CALLBACK:
            event_type = payload_event_type

            # Message event is from channel
            if (
                event_type == EventType.MESSAGE
                and payload_event_channel_type == EventType.MESSAGE_CHANNEL
                and (
                    not payload_event_subtype
                    or payload_event_subtype
                    in [
                        MessageEventSubtype.BOT_MESSAGE,
                        MessageEventSubtype.MESSAGE_CHANGED,
                        MessageEventSubtype.MESSAGE_DELETED,
                    ]
                )
            ):
                for route in SCENARIOS_ROUTES:
                    if payload_event_channel_type == route.get("message_channel_type"):
                        Step = route["step"]
                        logger.info("Routing to {}".format(Step))
                        step = Step(slack_team_identity, organization, user)
                        step.process_scenario(slack_user_identity, slack_team_identity, payload)
                        step_was_found = True
            # We don't do anything on app mention, but we doesn't want to unsubscribe from this event yet.
            if event_type == EventType.APP_MENTION:
                logger.info(f"Received event of type {EventType.APP_MENTION} from slack. Skipping.")
                return Response(status=200)

        # Routing to Steps based on routing rules
        if not step_was_found:
            for route in SCENARIOS_ROUTES:
                route_payload_type = route["payload_type"]

                # Slash commands have to "type"
                if payload_command and route_payload_type == PayloadType.SLASH_COMMAND:
                    cmd = SlashCommand.parse(payload)
                    # Check both command and subcommand for backward compatibility
                    # So both /grafana escalate and /escalate will work.
                    if cmd.command in route["command_name"] or cmd.subcommand in route["command_name"]:
                        Step = route["step"]
                        logger.info("Routing to {}".format(Step))
                        step = Step(slack_team_identity, organization, user)
                        step.process_scenario(slack_user_identity, slack_team_identity, payload)
                        step_was_found = True

                if payload_type == route_payload_type:
                    if payload_type == PayloadType.EVENT_CALLBACK:
                        if payload_event_type == route["event_type"]:
                            # event_name is used for stateful
                            if "event_name" not in route:
                                Step = route["step"]
                                logger.info("Routing to {}".format(Step))
                                step = Step(slack_team_identity, organization, user)
                                step.process_scenario(slack_user_identity, slack_team_identity, payload)
                                step_was_found = True

                    if payload_type == PayloadType.INTERACTIVE_MESSAGE:
                        for action in payload_actions:
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

                    if payload_type_is_block_actions:
                        for action in payload_actions:
                            if action["type"] == route["block_action_type"]:
                                if action["action_id"].startswith(route["block_action_id"]):
                                    Step = route["step"]
                                    logger.info("Routing to {}".format(Step))
                                    step = Step(slack_team_identity, organization, user)
                                    step.process_scenario(slack_user_identity, slack_team_identity, payload)
                                    step_was_found = True

                    if payload_type == PayloadType.DIALOG_SUBMISSION:
                        if payload_callback_id == route["dialog_callback_id"]:
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            result = step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            if result is not None:
                                return result
                            step_was_found = True

                    if payload_type == PayloadType.VIEW_SUBMISSION:
                        if payload["view"]["callback_id"].startswith(route["view_callback_id"]):
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            result = step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            if result is not None:
                                return result
                            step_was_found = True

                    if payload_type == PayloadType.MESSAGE_ACTION:
                        if payload_callback_id in route["message_action_callback_id"]:
                            Step = route["step"]
                            logger.info("Routing to {}".format(Step))
                            step = Step(slack_team_identity, organization, user)
                            step.process_scenario(slack_user_identity, slack_team_identity, payload)
                            step_was_found = True

        if not step_was_found:
            raise Exception("Step is undefined" + str(payload))

        return Response(status=200)

    @staticmethod
    def _get_slack_team_identity_from_payload(payload: EventPayload) -> SlackTeamIdentity | None:
        def _slack_team_id() -> str | None:
            with suppress(KeyError):
                return payload["team"]["id"]

            with suppress(KeyError):
                return payload["team_id"]

            return None

        try:
            return SlackTeamIdentity.objects.get(slack_id=_slack_team_id())
        except SlackTeamIdentity.DoesNotExist:
            return None

    @staticmethod
    def _get_organization_from_payload(
        payload: EventPayload, slack_team_identity: SlackTeamIdentity
    ) -> Organization | None:
        """
        Extract organization from Slack payload.
        First try to get "organization_id" from the payload, for cases when it was explicitly passed from elsewhere.
        Then try to find appropriate SlackMessage associated with the payload and get organization from it.
        """

        def _organization_id() -> str | int | None:
            with suppress(KeyError, TypeError, json.JSONDecodeError):
                return json.loads(payload["view"]["private_metadata"])["organization_id"]

            with suppress(KeyError, IndexError, TypeError, json.JSONDecodeError):
                return json.loads(payload["actions"][0]["value"])["organization_id"]

            return None

        with suppress(ObjectDoesNotExist):
            # see this GitHub issue for more context on how this situation can arise
            # https://github.com/grafana/oncall-private/issues/1836
            return slack_team_identity.organizations.get(pk=_organization_id())

        def _channel_id() -> str | None:
            with suppress(KeyError):
                return payload["channel"]["id"]

            with suppress(KeyError):
                return payload["event"]["channel"]

            with suppress(KeyError):
                return payload["channel_id"]

            return None

        def _message_ts() -> str | None:
            with suppress(KeyError):
                return payload["message"]["thread_ts"]

            with suppress(KeyError):
                return payload["message"]["ts"]

            with suppress(KeyError):
                return payload["message_ts"]

            with suppress(KeyError):
                return payload["event"]["message"]["thread_ts"]

            with suppress(KeyError):
                return payload["event"]["message"]["ts"]

            with suppress(KeyError):
                return payload["event"]["thread_ts"]

            return None

        channel_id, message_ts = _channel_id(), _message_ts()
        if not (channel_id and message_ts):
            return None

        try:
            slack_message = SlackMessage.objects.get(
                _slack_team_identity=slack_team_identity,
                slack_id=message_ts,
                channel_id=channel_id,
            )
        except SlackMessage.DoesNotExist:
            return None

        return slack_message.alert_group.channel.organization if slack_message.alert_group else None

    def _open_warning_window_if_needed(
        self, payload: EventPayload, slack_team_identity: SlackTeamIdentity, warning_text: str
    ) -> None:
        if payload.get("trigger_id") is not None:
            step = ScenarioStep(slack_team_identity)
            try:
                step.open_warning_window(payload, warning_text)
            except SlackAPIError as e:
                logger.info(
                    f"Failed to open pop-up for unpopulated SlackTeamIdentity {slack_team_identity.pk}\n" f"Error: {e}"
                )

    def _open_warning_for_unconnected_user(self, slack_client: SlackClient, payload: EventPayload) -> None:
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
        slack_client.views_open(trigger_id=payload["trigger_id"], view=view)


class ResetSlackView(APIView):
    permission_classes = (IsAuthenticated, RBACPermission)
    authentication_classes = [PluginAuthentication]

    rbac_permissions = {
        "post": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    def post(self, request):
        # TODO: this check should be removed once Unified Slack App is release
        if settings.SLACK_INTEGRATION_MAINTENANCE_ENABLED:
            return Response(
                "Grafana OnCall is temporary unable to connect your slack account or install OnCall to your slack workspace",
                status=400,
            )
        try:
            uninstall_slack_integration(request.user.organization, request.user)
        except SlackInstallationExc as e:
            return Response({"error": e.error_message}, status=400)
        return Response(status=200)
