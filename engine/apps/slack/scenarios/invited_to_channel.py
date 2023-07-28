import logging
import typing

from django.utils import timezone

from apps.slack.scenarios import scenario_step
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.types import EventPayload, EventType, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InvitedToChannelStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        if payload["event"]["user"] == slack_team_identity.bot_user_id:
            channel_id = payload["event"]["channel"]
            slack_client = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
            channel = slack_client.api_call("conversations.info", channel=channel_id)["channel"]

            slack_team_identity.cached_channels.update_or_create(
                slack_id=channel["id"],
                defaults={
                    "name": channel["name"],
                    "is_archived": channel["is_archived"],
                    "is_shared": channel["is_shared"],
                    "last_populated": timezone.now().date(),
                },
            )
        else:
            logger.info("Other user was invited to a channel with a bot.")


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.MEMBER_JOINED_CHANNEL,
        "step": InvitedToChannelStep,
    },
]
