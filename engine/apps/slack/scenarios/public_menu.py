import json
import logging

from django.apps import apps
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from apps.slack.scenarios import scenario_step
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException

from .step_mixins import CheckAlertIsUnarchivedMixin

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InvitedToChannelStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
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


class CloseEphemeralButtonStep(scenario_step.ScenarioStep):

    random_prefix_for_routing = "qwe2id"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        return JsonResponse({"response_type": "ephemeral", "delete_original": True})


# CreateIncidentManuallyStep trigger creation of a manual incident via slash command
class CreateIncidentManuallyStep(scenario_step.ScenarioStep):
    command_name = [settings.SLACK_SLASH_COMMAND_NAME]
    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    TITLE_INPUT_BLOCK_ID = "TITLE_INPUT"
    MESSAGE_INPUT_BLOCK_ID = "MESSAGE_INPUT"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        try:
            channel_id = payload["event"]["channel"]
        except KeyError:
            channel_id = payload["channel_id"]

        blocks = self.get_create_incident_blocks(payload, slack_team_identity, slack_user_identity)

        view = {
            "type": "modal",
            "callback_id": FinishCreateIncidentViewStep.routing_uid(),
            "title": {
                "type": "plain_text",
                "text": "Create an Incident",
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
            "private_metadata": json.dumps({"channel_id": channel_id}),
        }
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )

    def get_create_incident_blocks(self, payload, slack_team_identity, slack_user_identity):
        blocks = []
        organization_selection_block = self.get_select_organization_route_element(
            slack_team_identity, slack_user_identity
        )
        title_incident_block = {
            "type": "input",
            "block_id": self.TITLE_INPUT_BLOCK_ID,
            "label": {
                "type": "plain_text",
                "text": "Title:",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": FinishCreateIncidentViewStep.routing_uid(),
                "placeholder": {
                    "type": "plain_text",
                    "text": " ",
                },
            },
        }
        if payload.get("text", None) is not None:
            title_incident_block["element"]["initial_value"] = payload["text"]
        message_incident_block = {
            "type": "input",
            "block_id": self.MESSAGE_INPUT_BLOCK_ID,
            "label": {
                "type": "plain_text",
                "text": "Message:",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": FinishCreateIncidentViewStep.routing_uid(),
                "multiline": True,
                "placeholder": {
                    "type": "plain_text",
                    "text": " ",
                },
            },
            "optional": True,
        }
        if payload.get("message", {}).get("text") is not None:
            message_incident_block["element"]["initial_value"] = payload["message"]["text"]

        blocks.append(organization_selection_block)
        blocks.append(title_incident_block)
        blocks.append(message_incident_block)
        return blocks


# FinishCreateIncidentViewStep creates a manual incident via slash command
class FinishCreateIncidentViewStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
        ChannelFilter = apps.get_model("alerts", "ChannelFilter")

        Alert = apps.get_model("alerts", "Alert")
        payload_values = payload["view"]["state"]["values"]
        title = payload_values[CreateIncidentManuallyStep.TITLE_INPUT_BLOCK_ID][self.routing_uid()]["value"]
        text = payload_values[CreateIncidentManuallyStep.MESSAGE_INPUT_BLOCK_ID][self.routing_uid()]["value"] or ""

        private_metadata = json.loads(payload["view"]["private_metadata"])
        # update private metadata in payload to use it in alert rendering
        payload["view"]["private_metadata"] = private_metadata

        channel_id = private_metadata["channel_id"]

        alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
            organization=self.organization,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={"author": self.user},
        )
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
        user_verbal = self.user.get_user_verbal_for_team_for_slack()
        channel_filter_pk = payload["view"]["state"]["values"][
            scenario_step.ScenarioStep.SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID
        ][scenario_step.ScenarioStep.SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID]["selected_option"]["value"].split("-")[1]
        channel_filter = ChannelFilter.objects.get(pk=channel_filter_pk)
        Alert.create(
            title=title,
            message="{} created by {}".format(
                text,
                user_verbal,
            ),
            image_url=None,
            link_to_upstream_details=None,
            alert_receive_channel=alert_receive_channel,
            raw_request_data=payload,
            integration_unique_data={
                "created_by": user_verbal,
            },
            force_route_id=channel_filter.pk,
        )


# CreateIncidentSubmenuStep trigger creation of a manual incident via submenu
class CreateIncidentSubmenuStep(scenario_step.ScenarioStep):
    callback_id = [
        "incident_create",
        "incident_create_staging",
        "incident_create_develop",
    ]
    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        try:
            image_url = payload["message"]["files"][0]["permalink"]
        except KeyError:
            image_url = None
        channel_id = payload["channel"]["id"]

        private_metadata = {
            "channel_id": channel_id,
            "image_url": image_url,
            "message": {
                "user": payload["message"].get("user"),
                "text": payload["message"].get("text"),
                "ts": payload["message"].get("ts"),
            },
        }

        organization_selection_block = self.get_select_organization_route_element(
            slack_team_identity, slack_user_identity
        )
        view = {
            "type": "modal",
            "callback_id": FinishCreateIncidentSubmenuStep.routing_uid(),
            "title": {
                "type": "plain_text",
                "text": "Create an Incident",
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
            "blocks": [organization_selection_block],
            "private_metadata": json.dumps(private_metadata),
        }
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


# FinishCreateIncidentSubmenuStep creates a manual incident via submenu
class FinishCreateIncidentSubmenuStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
        Alert = apps.get_model("alerts", "Alert")

        private_metadata = json.loads(payload["view"]["private_metadata"])
        # update private metadata in payload to use it in alert rendering
        payload["view"]["private_metadata"] = private_metadata

        channel_id = private_metadata["channel_id"]
        author = private_metadata["message"]["user"]

        alert_receive_channel = AlertReceiveChannel.get_or_create_manual_integration(
            organization=self.organization,
            integration=AlertReceiveChannel.INTEGRATION_MANUAL,
            deleted_at=None,
            defaults={"author": self.user},
        )

        author_username = "Unknown"
        if author:
            try:
                author_username = self._slack_client.api_call(
                    "users.info",
                    user=author,
                )
                author_username = author_username.get("user", {}).get("real_name", None)
            except SlackAPIException:
                pass
        payload["view"]["private_metadata"]["author_username"] = author_username

        try:
            permalink = self._slack_client.api_call(
                "chat.getPermalink",
                channel=private_metadata["channel_id"],
                message_ts=private_metadata["message"]["ts"],
            )
            permalink = permalink.get("permalink", None)
        except SlackAPIException:
            permalink = None
        channel_filter_pk = payload["view"]["state"]["values"][
            scenario_step.ScenarioStep.SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID
        ][scenario_step.ScenarioStep.SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID]["selected_option"]["value"].split("-")[1]

        permalink = "<{}|Original message...>".format(permalink) if permalink is not None else ""
        Alert.create(
            title="Message from {}".format(author_username),
            message="{}\n{}".format(private_metadata["message"]["text"], permalink),
            image_url=private_metadata["image_url"],
            # Link to the slack message is not here bc it redirects to browser
            link_to_upstream_details=None,
            alert_receive_channel=alert_receive_channel,
            raw_request_data=payload,
            integration_unique_data={"created_by": self.user.get_user_verbal_for_team_for_slack()},
            force_route_id=channel_filter_pk,
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


class AddToResolutionoteStep(CheckAlertIsUnarchivedMixin, scenario_step.ScenarioStep):
    callback_id = [
        "add_resolution_note",
        "add_resolution_note_staging",
        "add_resolution_note_develop",
    ]
    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        SlackMessage = apps.get_model("slack", "SlackMessage")
        ResolutionNoteSlackMessage = apps.get_model("alerts", "ResolutionNoteSlackMessage")
        ResolutionNote = apps.get_model("alerts", "ResolutionNote")
        SlackUserIdentity = apps.get_model("slack", "SlackUserIdentity")

        try:
            channel_id = payload["channel"]["id"]
        except KeyError:
            raise Exception("Channel was not found")

        warning_text = "Unable to add this message to resolution note, this command works only in incident threads."

        try:
            slack_message = SlackMessage.objects.get(
                slack_id=payload["message"]["thread_ts"],
                _slack_team_identity=slack_team_identity,
                channel_id=channel_id,
            )
        except KeyError:
            self.open_warning_window(payload, warning_text)
            return
        except SlackMessage.DoesNotExist:
            self.open_warning_window(payload, warning_text)
            return

        try:
            alert_group = slack_message.get_alert_group()
        except SlackMessage.alert.RelatedObjectDoesNotExist as e:
            self.open_warning_window(payload, warning_text)
            print(
                f"Exception: tried to add message from thread to Resolution Note: "
                f"Slack Team Identity pk: {self.slack_team_identity.pk}, "
                f"Slack Message id: {slack_message.slack_id}"
            )
            raise e

        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return

        if payload["message"]["type"] == "message" and "user" in payload["message"]:
            message_ts = payload["message_ts"]
            thread_ts = payload["message"]["thread_ts"]

            result = self._slack_client.api_call(
                "chat.getPermalink",
                channel=channel_id,
                message_ts=message_ts,
            )
            permalink = None
            if result["permalink"] is not None:
                permalink = result["permalink"]

            if payload["message"]["ts"] in [
                message.ts
                for message in alert_group.resolution_note_slack_messages.filter(added_to_resolution_note=True)
            ]:
                warning_text = "Unable to add the same message again."
                self.open_warning_window(payload, warning_text)
                return

            elif len(payload["message"]["text"]) > 2900:
                warning_text = (
                    "Unable to add the message to Resolution note: the message is too long ({}). "
                    "Max length - 2900 symbols.".format(len(payload["message"]["text"]))
                )
                self.open_warning_window(payload, warning_text)
                return

            else:
                try:
                    resolution_note_slack_message = ResolutionNoteSlackMessage.objects.get(
                        ts=message_ts, thread_ts=thread_ts
                    )
                except ResolutionNoteSlackMessage.DoesNotExist:
                    text = payload["message"]["text"]
                    text = text.replace("```", "")
                    slack_message = SlackMessage.objects.get(
                        slack_id=thread_ts,
                        _slack_team_identity=slack_team_identity,
                        channel_id=channel_id,
                    )
                    alert_group = slack_message.get_alert_group()
                    author_slack_user_identity = SlackUserIdentity.objects.get(
                        slack_id=payload["message"]["user"], slack_team_identity=slack_team_identity
                    )
                    author_user = self.organization.users.get(slack_user_identity=author_slack_user_identity)
                    resolution_note_slack_message = ResolutionNoteSlackMessage(
                        alert_group=alert_group,
                        user=author_user,
                        added_by_user=self.user,
                        text=text,
                        slack_channel_id=channel_id,
                        thread_ts=thread_ts,
                        ts=message_ts,
                        permalink=permalink,
                    )
                resolution_note_slack_message.added_to_resolution_note = True
                resolution_note_slack_message.save()
                resolution_note = resolution_note_slack_message.get_resolution_note()
                if resolution_note is None:
                    ResolutionNote(
                        alert_group=alert_group,
                        author=resolution_note_slack_message.user,
                        source=ResolutionNote.Source.SLACK,
                        resolution_note_slack_message=resolution_note_slack_message,
                    ).save()
                else:
                    resolution_note.recreate()
                alert_group.drop_cached_after_resolve_report_json()
                alert_group.schedule_cache_for_web()
                try:
                    self._slack_client.api_call(
                        "reactions.add",
                        channel=channel_id,
                        name="memo",
                        timestamp=resolution_note_slack_message.ts,
                    )
                except SlackAPIException:
                    pass

                self._update_slack_message(alert_group)
        else:
            warning_text = "Unable to add this message to resolution note."
            self.open_warning_window(payload, warning_text)
            return


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_SLASH_COMMAND,
        "command_name": CreateIncidentManuallyStep.command_name,
        "step": CreateIncidentManuallyStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_MEMBER_JOINED_CHANNEL,
        "step": InvitedToChannelStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": CloseEphemeralButtonStep.routing_uid(),
        "step": CloseEphemeralButtonStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": FinishCreateIncidentViewStep.routing_uid(),
        "step": FinishCreateIncidentViewStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": FinishCreateIncidentSubmenuStep.routing_uid(),
        "step": FinishCreateIncidentSubmenuStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_MESSAGE_ACTION,
        "message_action_callback_id": CreateIncidentSubmenuStep.callback_id,
        "step": CreateIncidentSubmenuStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_MESSAGE_ACTION,
        "message_action_callback_id": AddToResolutionoteStep.callback_id,
        "step": AddToResolutionoteStep,
    },
]
