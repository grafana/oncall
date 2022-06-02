from contextlib import suppress

from django.apps import apps
from django.utils import timezone

from apps.slack.scenarios import scenario_step


class SlackChannelCreatedOrRenamedEventStep(scenario_step.ScenarioStep):
    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    # Avoid logging this step to prevent collecting sensitive data of our customers
    need_to_be_logged = False

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        """
        Triggered by action: Create or rename channel
        """
        SlackChannel = apps.get_model("slack", "SlackChannel")

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
    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    # Avoid logging this step to prevent collecting sensitive data of our customers
    need_to_be_logged = False

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        """
        Triggered by action: Delete channel
        """
        SlackChannel = apps.get_model("slack", "SlackChannel")

        slack_id = payload["event"]["channel"]
        with suppress(SlackChannel.DoesNotExist):
            SlackChannel.objects.get(
                slack_id=slack_id,
                slack_team_identity=slack_team_identity,
            ).delete()


class SlackChannelArchivedEventStep(scenario_step.ScenarioStep):
    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    # Avoid logging this step to prevent collecting sensitive data of our customers
    need_to_be_logged = False

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        """
        Triggered by action: Archive channel
        """
        SlackChannel = apps.get_model("slack", "SlackChannel")

        slack_id = payload["event"]["channel"]

        SlackChannel.objects.filter(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
        ).update(is_archived=True)


class SlackChannelUnArchivedEventStep(scenario_step.ScenarioStep):
    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    # Avoid logging this step to prevent collecting sensitive data of our customers
    need_to_be_logged = False

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        """
        Triggered by action: UnArchive channel
        """
        SlackChannel = apps.get_model("slack", "SlackChannel")

        slack_id = payload["event"]["channel"]

        SlackChannel.objects.filter(
            slack_id=slack_id,
            slack_team_identity=slack_team_identity,
        ).update(is_archived=False)


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_CHANNEL_RENAMED,
        "step": SlackChannelCreatedOrRenamedEventStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_CHANNEL_CREATED,
        "step": SlackChannelCreatedOrRenamedEventStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_CHANNEL_DELETED,
        "step": SlackChannelDeletedEventStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_CHANNEL_ARCHIVED,
        "step": SlackChannelArchivedEventStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_CHANNEL_UNARCHIVED,
        "step": SlackChannelUnArchivedEventStep,
    },
]
