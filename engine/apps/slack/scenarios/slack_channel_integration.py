import logging
import typing

from apps.slack.scenarios import scenario_step
from apps.slack.types import EventPayload, EventType, MessageEventSubtype, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackChannelMessageEventStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Triggered by action: Any new message in channel.
        Dangerous because it's often triggered by internal client's company systems.
        May cause flood, should be ready for useless updates.
        """

        # If it is a message from thread - save it for resolution note
        if ("thread_ts" in payload["event"] and "subtype" not in payload["event"]) or (
            payload["event"].get("subtype") == MessageEventSubtype.MESSAGE_CHANGED
            and "subtype" not in payload["event"]["message"]
            and "thread_ts" in payload["event"]["message"]
        ):
            self.save_thread_message_for_resolution_note(slack_user_identity, payload)
        elif (
            payload["event"].get("subtype") == MessageEventSubtype.MESSAGE_DELETED
            and "thread_ts" in payload["event"]["previous_message"]
        ):
            self.delete_thread_message_from_resolution_note(slack_user_identity, payload)

    def save_thread_message_for_resolution_note(
        self, slack_user_identity: "SlackUserIdentity", payload: EventPayload
    ) -> None:
        from apps.alerts.models import ResolutionNoteSlackMessage
        from apps.slack.models import SlackMessage

        if slack_user_identity is None:
            logger.warning(
                f"Empty slack_user_identity in PublicMainMenu step:\n"
                f"{self.slack_team_identity} {self.slack_team_identity.pk}"
            )
            return

        channel = payload["event"]["channel"]
        thread_ts = payload["event"].get("thread_ts") or payload["event"]["message"]["thread_ts"]
        # sometimes we get messages with empty text, probably because it's an image or attachment
        event_text = payload["event"].get("text")
        event_text = "empty message" if event_text == "" else event_text
        text = event_text or payload["event"]["message"]["text"]

        if "message" in payload["event"]:
            message_ts = payload["event"]["message"]["ts"]
        else:
            message_ts = payload["event"]["ts"]

        try:
            slack_message = SlackMessage.objects.get(
                slack_id=thread_ts,
                channel_id=channel,
                _slack_team_identity=self.slack_team_identity,
            )
        except SlackMessage.DoesNotExist:
            return

        alert_group = slack_message.get_alert_group()

        result = self._slack_client.api_call(
            "chat.getPermalink",
            channel=channel,
            message_ts=message_ts,
        )
        permalink = None
        if result["permalink"] is not None:
            permalink = result["permalink"]

        try:
            slack_thread_message = ResolutionNoteSlackMessage.objects.get(
                ts=message_ts,
                thread_ts=thread_ts,
                alert_group=alert_group,
            )
            if len(text) > 2900:
                if slack_thread_message.added_to_resolution_note:
                    self._slack_client.api_call(
                        "chat.postEphemeral",
                        channel=channel,
                        user=slack_user_identity.slack_id,
                        text=":warning: Unable to update the <{}|message> in Resolution Note: the message is too long ({}). "
                        "Max length - 2900 symbols.".format(permalink, len(text)),
                    )
                return
            slack_thread_message.text = text
            slack_thread_message.save()

        except ResolutionNoteSlackMessage.DoesNotExist:
            if len(text) > 2900:
                self._slack_client.api_call(
                    "chat.postEphemeral",
                    channel=channel,
                    user=slack_user_identity.slack_id,
                    text=":warning: The <{}|message> will not be displayed in Resolution Note: "
                    "the message is too long ({}). Max length - 2900 symbols.".format(permalink, len(text)),
                )
                return

            slack_thread_message = ResolutionNoteSlackMessage(
                alert_group=alert_group,
                user=self.user,
                added_by_user=self.user,
                text=text,
                slack_channel_id=channel,
                thread_ts=thread_ts,
                ts=message_ts,
                permalink=permalink,
            )
            slack_thread_message.save()

    def delete_thread_message_from_resolution_note(
        self, slack_user_identity: "SlackUserIdentity", payload: EventPayload
    ) -> None:
        from apps.alerts.models import ResolutionNoteSlackMessage

        if slack_user_identity is None:
            logger.warning(
                f"Empty slack_user_identity in PublicMainMenu step:\n"
                f"{self.slack_team_identity} {self.slack_team_identity.pk}"
            )
            return

        channel_id = payload["event"]["channel"]
        message_ts = payload["event"]["previous_message"]["ts"]
        thread_ts = payload["event"]["previous_message"]["thread_ts"]
        try:
            slack_thread_message = ResolutionNoteSlackMessage.objects.get(
                ts=message_ts,
                thread_ts=thread_ts,
                slack_channel_id=channel_id,
            )
        except ResolutionNoteSlackMessage.DoesNotExist:
            pass
        else:
            alert_group = slack_thread_message.alert_group
            slack_thread_message.delete()
            self.alert_group_slack_service.update_alert_group_slack_message(alert_group)


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    typing.cast(
        ScenarioRoute.EventCallbackChannelMessageScenarioRoute,
        {
            "payload_type": PayloadType.EVENT_CALLBACK,
            "event_type": EventType.MESSAGE,
            "message_channel_type": EventType.MESSAGE_CHANNEL,
            "step": SlackChannelMessageEventStep,
        },
    ),
]
