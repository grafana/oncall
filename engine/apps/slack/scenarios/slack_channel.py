import typing
from contextlib import suppress

from django.utils import timezone

from apps.slack.scenarios import scenario_step
from apps.slack.tasks import clean_slack_channel_leftovers
from apps.slack.types import EventPayload, EventType, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class SlackChannelCreatedOrRenamedEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: Create or rename channel
        """
        from apps.slack.models import SlackChannel

        slack_id = payload["event"]["channel"]["id"]
        channel_name = payload["event"]["channel"]["name"]

        SlackChannel.objects.update_or_create(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
            defaults={
                "name": channel_name,
                "last_populated": timezone.now().date(),
            },
        )


class SlackChannelDeletedEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: Delete channel
        """
        from apps.slack.models import SlackChannel

        slack_id = payload["event"]["channel"]
        with suppress(SlackChannel.DoesNotExist):
            SlackChannel.objects.get(
                slack_id=slack_id,
                slack_team_identity=slack_team_identity,
            ).delete()
        # even if channel is deteletd run the task to clean possible leftowers
        clean_slack_channel_leftovers.apply_async((slack_team_identity.id, slack_id))


class SlackChannelArchivedEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: Archive channel
        """
        from apps.slack.models import SlackChannel

        slack_id = payload["event"]["channel"]

        SlackChannel.objects.filter(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
        ).update(is_archived=True)
        clean_slack_channel_leftovers.apply_async((slack_team_identity.id, slack_id))


class SlackChannelUnArchivedEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: UnArchive channel
        """
        from apps.slack.models import SlackChannel

        slack_id = payload["event"]["channel"]

        SlackChannel.objects.filter(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
        ).update(is_archived=False)


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.CHANNEL_RENAMED,
        "step": SlackChannelCreatedOrRenamedEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.CHANNEL_CREATED,
        "step": SlackChannelCreatedOrRenamedEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.CHANNEL_DELETED,
        "step": SlackChannelDeletedEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.CHANNEL_ARCHIVED,
        "step": SlackChannelArchivedEventStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.CHANNEL_UNARCHIVED,
        "step": SlackChannelUnArchivedEventStep,
    },
]
