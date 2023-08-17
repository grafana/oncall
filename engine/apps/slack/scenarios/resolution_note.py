import datetime
import json
import logging
import typing

from django.db.models import Q

from apps.api.permissions import RBACPermission
from apps.slack.constants import DIVIDER
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException
from apps.slack.types import (
    Block,
    BlockActionType,
    EventPayload,
    InteractiveMessageActionType,
    PayloadType,
    ScenarioRoute,
)
from apps.user_management.models import User
from common.api_helpers.utils import create_engine_url

from .step_mixins import AlertGroupActionsMixin

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, ResolutionNote, ResolutionNoteSlackMessage
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AddToResolutionNoteStep(scenario_step.ScenarioStep):
    callback_id = [
        "add_resolution_note",
        "add_resolution_note_staging",
        "add_resolution_note_develop",
    ]

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        from apps.alerts.models import ResolutionNote, ResolutionNoteSlackMessage
        from apps.slack.models import SlackMessage, SlackUserIdentity

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
                    try:
                        author_slack_user_identity = SlackUserIdentity.objects.get(
                            slack_id=payload["message"]["user"], slack_team_identity=slack_team_identity
                        )
                        author_user = self.organization.users.get(slack_user_identity=author_slack_user_identity)
                    except (SlackUserIdentity.DoesNotExist, User.DoesNotExist):
                        warning_text = (
                            "Unable to add this message to resolution note: could not find corresponding "
                            "OnCall user for message author: {}".format(payload["message"]["user"])
                        )
                        self.open_warning_window(payload, warning_text)
                        return
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
                try:
                    self._slack_client.api_call(
                        "reactions.add",
                        channel=channel_id,
                        name="memo",
                        timestamp=resolution_note_slack_message.ts,
                    )
                except SlackAPIException:
                    pass

                self.alert_group_slack_service.update_alert_group_slack_message(alert_group)
        else:
            warning_text = "Unable to add this message to resolution note."
            self.open_warning_window(payload, warning_text)
            return


class UpdateResolutionNoteStep(scenario_step.ScenarioStep):
    def process_signal(self, alert_group: "AlertGroup", resolution_note: "ResolutionNote") -> None:
        if resolution_note.deleted_at:
            self.remove_resolution_note_slack_message(resolution_note)
        else:
            self.post_or_update_resolution_note_in_thread(resolution_note)

        self.update_alert_group_resolution_note_button(
            alert_group=alert_group,
        )

    def remove_resolution_note_slack_message(self, resolution_note: "ResolutionNote") -> None:
        resolution_note_slack_message = resolution_note.resolution_note_slack_message
        if resolution_note_slack_message is not None:
            resolution_note_slack_message.added_to_resolution_note = False
            resolution_note_slack_message.save(update_fields=["added_to_resolution_note"])
            if resolution_note_slack_message.posted_by_bot:
                try:
                    self._slack_client.api_call(
                        "chat.delete",
                        channel=resolution_note_slack_message.slack_channel_id,
                        ts=resolution_note_slack_message.ts,
                    )
                except SlackAPIException as e:
                    if e.response["error"] == "channel_not_found":
                        logger.warning(
                            f"Unable to delete resolution note message in slack. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"Reason: 'channel_not_found'"
                        )
                    elif e.response["error"] == "message_not_found":
                        logger.warning(
                            f"Unable to delete resolution note message in slack. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"Reason: 'message_not_found'"
                        )
                    elif e.response["error"] == "is_archived":
                        logger.warning(
                            f"Unable to delete resolution note message in slack. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"Reason: 'is_archived'"
                        )
                    elif e.response["error"] == "invalid_auth":
                        logger.warning(
                            f"Unable to delete resolution note message in slack. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"Reason: 'invalid_auth'"
                        )
                    elif e.response["error"] == "is_inactive":
                        logger.warning(
                            f"Unable to delete resolution note message in slack. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"Reason: 'is_inactive'"
                        )
                    else:
                        raise e
            else:
                self.remove_resolution_note_reaction(resolution_note_slack_message)

    def post_or_update_resolution_note_in_thread(self, resolution_note: "ResolutionNote") -> None:
        from apps.alerts.models import ResolutionNoteSlackMessage

        resolution_note_slack_message = resolution_note.resolution_note_slack_message
        alert_group = resolution_note.alert_group
        alert_group_slack_message = alert_group.slack_message
        blocks = self.get_resolution_note_blocks(resolution_note)

        if resolution_note_slack_message is None:
            try:
                result = self._slack_client.api_call(
                    "chat.postMessage",
                    channel=alert_group_slack_message.channel_id,
                    thread_ts=alert_group_slack_message.slack_id,
                    text=resolution_note.text,
                    blocks=blocks,
                )
            except SlackAPIException as e:
                if e.response["error"] == "channel_not_found":
                    logger.warning(
                        f"Unable to post resolution note message to slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'channel_not_found'"
                    )
                elif e.response["error"] == "is_archived":
                    logger.warning(
                        f"Unable to post resolution note message to slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'is_archived'"
                    )
                elif e.response["error"] == "invalid_auth":
                    logger.warning(
                        f"Unable to post resolution note message to slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'invalid_auth'"
                    )
                else:
                    raise e
            else:
                message_ts = result["message"]["ts"]
                result_permalink = self._slack_client.api_call(
                    "chat.getPermalink",
                    channel=alert_group_slack_message.channel_id,
                    message_ts=message_ts,
                )

                resolution_note_slack_message = ResolutionNoteSlackMessage(
                    alert_group=alert_group,
                    user=resolution_note.author,
                    added_by_user=resolution_note.author,
                    text=resolution_note.text,
                    slack_channel_id=alert_group_slack_message.channel_id,
                    thread_ts=result["ts"],
                    ts=message_ts,
                    permalink=result_permalink["permalink"],
                    posted_by_bot=True,
                    added_to_resolution_note=True,
                )
                resolution_note_slack_message.save()
                self.add_resolution_note_reaction(resolution_note_slack_message)

                resolution_note.resolution_note_slack_message = resolution_note_slack_message
                resolution_note.save(update_fields=["resolution_note_slack_message"])
        elif resolution_note_slack_message.posted_by_bot:
            try:
                self._slack_client.api_call(
                    "chat.update",
                    channel=alert_group_slack_message.channel_id,
                    ts=resolution_note_slack_message.ts,
                    text=resolution_note_slack_message.text,
                    blocks=blocks,
                )
            except SlackAPIException as e:
                if e.response["error"] == "channel_not_found":
                    logger.warning(
                        f"Unable to update resolution note message in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'channel_not_found'"
                    )
                elif e.response["error"] == "message_not_found":
                    logger.warning(
                        f"Unable to update resolution note message in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'message_not_found'"
                    )
                elif e.response["error"] == "invalid_auth":
                    logger.warning(
                        f"Unable to update resolution note message in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'invalid_auth'"
                    )
                elif e.response["error"] == "is_inactive":
                    logger.warning(
                        f"Unable to update resolution note message in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'is_inactive'"
                    )
                elif e.response["error"] == "account_inactive":
                    logger.warning(
                        f"Unable to update resolution note message in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'account_inactive'"
                    )
                else:
                    raise e
            else:
                resolution_note_slack_message.text = resolution_note.text
                resolution_note_slack_message.save(update_fields=["text"])

    def update_alert_group_resolution_note_button(self, alert_group: "AlertGroup") -> None:
        if alert_group.slack_message is not None:
            self.alert_group_slack_service.update_alert_group_slack_message(alert_group)

    def add_resolution_note_reaction(self, slack_thread_message: "ResolutionNoteSlackMessage"):
        try:
            self._slack_client.api_call(
                "reactions.add",
                channel=slack_thread_message.slack_channel_id,
                name="memo",
                timestamp=slack_thread_message.ts,
            )
        except SlackAPIException as e:
            print(e)  # TODO:770: log instead of print

    def remove_resolution_note_reaction(self, slack_thread_message: "ResolutionNoteSlackMessage") -> None:
        try:
            self._slack_client.api_call(
                "reactions.remove",
                channel=slack_thread_message.slack_channel_id,
                name="memo",
                timestamp=slack_thread_message.ts,
            )
        except SlackAPIException as e:
            print(e)

    def get_resolution_note_blocks(self, resolution_note: "ResolutionNote") -> Block.AnyBlocks:
        blocks: Block.AnyBlocks = []
        author_verbal = resolution_note.author_verbal(mention=False)
        resolution_note_text_block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": resolution_note.text},
        }
        blocks.append(resolution_note_text_block)
        context_block = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{author_verbal} resolution note from {resolution_note.get_source_display()}.",
                }
            ],
        }
        blocks.append(context_block)
        return blocks


class ResolutionNoteModalStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.CHATOPS_WRITE]
    RESOLUTION_NOTE_TEXT_BLOCK_ID = "resolution_note_text"
    RESOLUTION_NOTE_MESSAGES_MAX_COUNT = 25

    class ScenarioData(typing.TypedDict):
        resolution_note_window_action: str
        alert_group_pk: str
        action_resolve: bool

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
        data: ScenarioData | None = None,
    ) -> None:
        if data:
            # Argument "data" is used when step is called from other step, e.g. AddRemoveThreadMessageStep
            from apps.alerts.models import AlertGroup

            alert_group = AlertGroup.objects.get(pk=data["alert_group_pk"])
        else:
            # Handle "Add Resolution notes" button click
            alert_group = self.get_alert_group(slack_team_identity, payload)

        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        value = data or json.loads(payload["actions"][0]["value"])
        resolution_note_window_action = value.get("resolution_note_window_action", "") or value.get("action_value", "")
        action_resolve = value.get("action_resolve", False)
        channel_id = payload["channel"]["id"] if "channel" in payload else None

        blocks: Block.AnyBlocks = []

        if channel_id:
            members = slack_team_identity.get_conversation_members(self._slack_client, channel_id)
            if slack_team_identity.bot_user_id not in members:
                blocks.extend(self.get_invite_bot_tip_blocks(channel_id))

        blocks.extend(
            self.get_resolution_notes_blocks(
                alert_group,
                resolution_note_window_action,
                action_resolve,
            )
        )

        view = {
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Resolution notes",
            },
            "private_metadata": json.dumps(
                {
                    "organization_id": self.organization.pk if self.organization else alert_group.organization.pk,
                    "alert_group_pk": alert_group.pk,
                }
            ),
        }

        if "update" in resolution_note_window_action:
            try:
                self._slack_client.api_call(
                    "views.update",
                    trigger_id=payload["trigger_id"],
                    view=view,
                    view_id=payload["view"]["id"],
                )
            except SlackAPIException as e:
                if e.response["error"] == "not_found":
                    # Ignore "not_found" error, it means that the view was closed by user before the update request.
                    # It doesn't disrupt the user experience.
                    logger.debug(
                        f"API call to views.update failed for alert group {alert_group.pk}, error: not_found. "
                        f"Most likely the view was closed by user before the request was processed. "
                    )
                else:
                    raise
        else:
            self._slack_client.api_call(
                "views.open",
                trigger_id=payload["trigger_id"],
                view=view,
            )

    def get_resolution_notes_blocks(
        self, alert_group: "AlertGroup", resolution_note_window_action: str, action_resolve: bool
    ) -> Block.AnyBlocks:
        from apps.alerts.models import ResolutionNote

        blocks: Block.AnyBlocks = []

        other_resolution_notes = alert_group.resolution_notes.filter(~Q(source=ResolutionNote.Source.SLACK))
        resolution_note_slack_messages = alert_group.resolution_note_slack_messages.filter(
            posted_by_bot=False
        ).order_by("-pk")
        if resolution_note_slack_messages.count() > self.RESOLUTION_NOTE_MESSAGES_MAX_COUNT:
            blocks.extend(
                [
                    DIVIDER,
                    typing.cast(
                        Block.Section,
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": (
                                    ":warning: Listing up to last {} thread messages, "
                                    "you can still add any other message using contextual menu actions."
                                ).format(self.RESOLUTION_NOTE_MESSAGES_MAX_COUNT),
                            },
                        },
                    ),
                ]
            )
        if action_resolve:
            blocks.extend(
                [
                    DIVIDER,
                    typing.cast(
                        Block.Section,
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": ":warning: You cannot resolve this incident without resolution note.",
                            },
                        },
                    ),
                ]
            )

        if "error" in resolution_note_window_action:
            blocks.extend(
                [
                    DIVIDER,
                    typing.cast(
                        Block.Section,
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": ":warning: _Oops! You cannot remove this message from resolution notes when incident is "
                                "resolved. Reason: `resolution note is required` setting. Add another message at first._ ",
                            },
                        },
                    ),
                ]
            )

        for message in resolution_note_slack_messages[: self.RESOLUTION_NOTE_MESSAGES_MAX_COUNT]:
            user_verbal = message.user.get_username_with_slack_verbal(mention=True)
            blocks.append(DIVIDER)
            message_block: Block.Section = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "{} <!date^{:.0f}^{{date_num}} {{time_secs}}|message_created_at>\n{}".format(
                        user_verbal,
                        float(message.ts),
                        message.text,
                    ),
                },
                "accessory": {
                    "type": "button",
                    "style": "primary" if not message.added_to_resolution_note else "danger",
                    "text": {
                        "type": "plain_text",
                        "text": "Add" if not message.added_to_resolution_note else "Remove",
                        "emoji": True,
                    },
                    "action_id": AddRemoveThreadMessageStep.routing_uid(),
                    "value": json.dumps(
                        {
                            "resolution_note_window_action": "edit",
                            "msg_value": "add" if not message.added_to_resolution_note else "remove",
                            "message_pk": message.pk,
                            "resolution_note_pk": None,
                            "alert_group_pk": alert_group.pk,
                        }
                    ),
                },
            }
            blocks.append(message_block)

        if other_resolution_notes:
            blocks.extend(
                [
                    DIVIDER,
                    typing.cast(
                        Block.Section,
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Resolution notes from other sources:*",
                            },
                        },
                    ),
                ]
            )
            for resolution_note in other_resolution_notes:
                resolution_note_slack_message = resolution_note.resolution_note_slack_message
                user_verbal = resolution_note.author_verbal(mention=True)
                message_timestamp = datetime.datetime.timestamp(resolution_note.created_at)
                blocks.append(DIVIDER)
                source = "web" if resolution_note.source == ResolutionNote.Source.WEB else "slack"

                blocks.append(
                    typing.cast(
                        Block.Section,
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "{} <!date^{:.0f}^{{date_num}} {{time_secs}}|note_created_at> (from {})\n{}".format(
                                    user_verbal,
                                    float(message_timestamp),
                                    source,
                                    resolution_note.message_text,
                                ),
                            },
                            "accessory": {
                                "type": "button",
                                "style": "danger",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Remove",
                                    "emoji": True,
                                },
                                "action_id": AddRemoveThreadMessageStep.routing_uid(),
                                "value": json.dumps(
                                    {
                                        "resolution_note_window_action": "edit",
                                        "msg_value": "remove",
                                        "message_pk": None
                                        if not resolution_note_slack_message
                                        else resolution_note_slack_message.pk,
                                        "resolution_note_pk": resolution_note.pk,
                                        "alert_group_pk": alert_group.pk,
                                    }
                                ),
                                "confirm": {
                                    "title": {"type": "plain_text", "text": "Are you sure?"},
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "This operation will permanently delete this Resolution Note.",
                                    },
                                    "confirm": {"type": "plain_text", "text": "Delete"},
                                    "deny": {
                                        "type": "plain_text",
                                        "text": "Stop, I've changed my mind!",
                                    },
                                    "style": "danger",
                                },
                            },
                        },
                    )
                )

        if not blocks:
            # there aren't any resolution notes yet, display a hint instead
            link_to_instruction = create_engine_url("static/images/postmortem.gif")
            blocks = [
                DIVIDER,
                typing.cast(
                    Block.Section,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":bulb: You can add a message to the resolution notes via context menu:",
                        },
                    },
                ),
                typing.cast(
                    Block.Image,
                    {
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": "Add a resolution note",
                        },
                        "image_url": link_to_instruction,
                        "alt_text": "Add to postmortem context menu",
                    },
                ),
            ]

        return blocks

    def get_invite_bot_tip_blocks(self, channel: str) -> Block.AnyBlocks:
        link_to_instruction = create_engine_url("static/images/postmortem.gif")
        blocks: Block.AnyBlocks = [
            DIVIDER,
            typing.cast(
                Block.Context,
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f":bulb: To include messages from thread to resolution note `/invite` Grafana OnCall to "
                            f"<#{channel}>. Or you can add a message via "
                            f"<{link_to_instruction}|context menu>.",
                        },
                    ],
                },
            ),
        ]
        return blocks


class ReadEditPostmortemStep(ResolutionNoteModalStep):
    # Left for backward compatibility with slack messages created before postmortems -> resolution note change
    pass


class AddRemoveThreadMessageStep(UpdateResolutionNoteStep, scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        from apps.alerts.models import AlertGroup, ResolutionNote, ResolutionNoteSlackMessage

        value = json.loads(payload["actions"][0]["value"])
        slack_message_pk = value.get("message_pk")
        resolution_note_pk = value.get("resolution_note_pk")
        alert_group_pk = value.get("alert_group_pk")
        add_to_resolution_note = True if value["msg_value"].startswith("add") else False
        slack_thread_message = None
        resolution_note = None

        alert_group = AlertGroup.objects.get(pk=alert_group_pk)

        if slack_message_pk is not None:
            slack_thread_message = ResolutionNoteSlackMessage.objects.get(pk=slack_message_pk)
            resolution_note = slack_thread_message.get_resolution_note()

        if add_to_resolution_note and slack_thread_message is not None:
            slack_thread_message.added_to_resolution_note = True
            slack_thread_message.save(update_fields=["added_to_resolution_note"])
            if resolution_note is None:
                ResolutionNote(
                    alert_group=alert_group,
                    author=slack_thread_message.user,
                    source=ResolutionNote.Source.SLACK,
                    resolution_note_slack_message=slack_thread_message,
                ).save()
            else:
                resolution_note.recreate()
            self.add_resolution_note_reaction(slack_thread_message)
        elif not add_to_resolution_note:
            # Check if resolution_note can be removed
            if (
                self.organization.is_resolution_note_required
                and alert_group.resolved
                and alert_group.resolution_notes.count() == 1
            ):
                # Show error message
                resolution_note_data = json.loads(payload["actions"][0]["value"])
                resolution_note_data["resolution_note_window_action"] = "edit_update_error"
                return ResolutionNoteModalStep(slack_team_identity, self.organization, self.user).process_scenario(
                    slack_user_identity,
                    slack_team_identity,
                    payload,
                    data=resolution_note_data,
                )
            else:
                if resolution_note_pk is not None and resolution_note is None:  # old version of step
                    resolution_note = ResolutionNote.objects.get(pk=resolution_note_pk)
                resolution_note.delete()
                if slack_thread_message:
                    slack_thread_message.added_to_resolution_note = False
                    slack_thread_message.save(update_fields=["added_to_resolution_note"])
                    self.remove_resolution_note_reaction(slack_thread_message)
        self.update_alert_group_resolution_note_button(
            alert_group,
        )
        resolution_note_data = json.loads(payload["actions"][0]["value"])
        resolution_note_data["resolution_note_window_action"] = "edit_update"
        ResolutionNoteModalStep(slack_team_identity, self.organization, self.user).process_scenario(
            slack_user_identity,
            slack_team_identity,
            payload,
            data=resolution_note_data,
        )


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": ReadEditPostmortemStep.routing_uid(),
        "step": ReadEditPostmortemStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": ResolutionNoteModalStep.routing_uid(),
        "step": ResolutionNoteModalStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": ResolutionNoteModalStep.routing_uid(),
        "step": ResolutionNoteModalStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": AddRemoveThreadMessageStep.routing_uid(),
        "step": AddRemoveThreadMessageStep,
    },
    {
        "payload_type": PayloadType.MESSAGE_ACTION,
        "message_action_callback_id": AddToResolutionNoteStep.callback_id,
        "step": AddToResolutionNoteStep,
    },
]
