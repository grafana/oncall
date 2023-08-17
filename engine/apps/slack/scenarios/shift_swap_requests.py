import json
import logging
import typing

import humanize
from django.utils import timezone

from apps.slack.constants import DIVIDER
from apps.slack.models import SlackMessage
from apps.slack.scenarios import scenario_step
from apps.slack.types import Block, BlockActionType, EventPayload, PayloadType, ScenarioRoute
from apps.slack.utils import SlackDateFormat, format_datetime_to_slack, format_datetime_to_slack_with_time

if typing.TYPE_CHECKING:
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SHIFT_SWAP_PK_ACTION_KEY = "shift_swap_request_pk"


class BaseShiftSwapRequestStep(scenario_step.ScenarioStep):
    def _generate_blocks(self, shift_swap_request: "ShiftSwapRequest") -> Block.AnyBlocks:
        pk = shift_swap_request.pk

        main_message_text = f"Your teammate {shift_swap_request.beneficiary.get_username_with_slack_verbal()} has submitted a shift swap request."

        datetime_format = SlackDateFormat.DATE_LONG_PRETTY
        time_format = SlackDateFormat.TIME

        shift_details = ""
        for shift in shift_swap_request.shifts():
            shift_start = shift["start"]
            shift_start_posix = shift_start.timestamp()
            shift_end = shift["end"]
            shift_end_posix = shift_end.timestamp()

            time_details = ""
            if shift_start.date() == shift_end.date():
                # shift starts and ends on the same day
                time_details = f"{format_datetime_to_slack_with_time(shift_start_posix, datetime_format)} - {format_datetime_to_slack(shift_end_posix, time_format)}"
            else:
                # shift starts and ends on different days
                time_details = f"{format_datetime_to_slack_with_time(shift_start_posix, datetime_format)} - {format_datetime_to_slack_with_time(shift_end_posix, datetime_format)}"

            shift_details += f"• {time_details}\n"

        blocks: Block.AnyBlocks = [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": main_message_text,
                    },
                },
            ),
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📅 Shift Details*:\n\n{shift_details}",
                    },
                },
            ),
        ]

        if description := shift_swap_request.description:
            blocks.append(
                typing.cast(
                    Block.Section,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📝 Description*: {description}",
                        },
                    },
                )
            )

        if shift_swap_request.is_deleted:
            blocks.append(
                typing.cast(
                    Block.Section,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Update*: this shift swap request has been deleted.",
                        },
                    },
                ),
            )
        elif shift_swap_request.is_taken:
            blocks.append(
                typing.cast(
                    Block.Section,
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Update*: {shift_swap_request.benefactor.get_username_with_slack_verbal()} has taken the shift swap.",
                        },
                    },
                ),
            )
        else:
            value = {
                SHIFT_SWAP_PK_ACTION_KEY: pk,
                "organization_id": shift_swap_request.organization.pk,
            }

            blocks.append(
                typing.cast(
                    Block.Actions,
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "style": "primary",
                                "text": {
                                    "type": "plain_text",
                                    "text": "✔️ Accept Shift Swap Request",
                                    "emoji": True,
                                },
                                "value": json.dumps(value),
                                "action_id": AcceptShiftSwapRequestStep.routing_uid(),
                            },
                        ],
                    },
                )
            )

        blocks.extend(
            [
                DIVIDER,
                typing.cast(
                    Block.Context,
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"👀 View the shift swap within Grafana OnCall by clicking <{shift_swap_request.web_link}|here>.",
                            },
                        ],
                    },
                ),
            ]
        )

        return blocks

    def create_message(self, shift_swap_request: "ShiftSwapRequest") -> SlackMessage:
        channel_id = shift_swap_request.slack_channel_id
        organization = self.organization

        blocks = self._generate_blocks(shift_swap_request)
        result = self._slack_client.api_call("chat.postMessage", channel=channel_id, blocks=blocks)

        return SlackMessage.objects.create(
            slack_id=result["ts"],
            organization=organization,
            _slack_team_identity=self.slack_team_identity,
            channel_id=channel_id,
        )

    def update_message(self, shift_swap_request: "ShiftSwapRequest") -> None:
        # TODO: better error handling here...
        self._slack_client.api_call(
            "chat.update",
            channel=shift_swap_request.slack_channel_id,
            ts=shift_swap_request.slack_message.slack_id,
            blocks=self._generate_blocks(shift_swap_request),
        )


class AcceptShiftSwapRequestStep(BaseShiftSwapRequestStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        from apps.schedules import exceptions
        from apps.schedules.models import ShiftSwapRequest

        shift_swap_request_pk = json.loads(payload["actions"][0]["value"])[SHIFT_SWAP_PK_ACTION_KEY]

        try:
            shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
        except ShiftSwapRequest.DoesNotExist:
            logger.info(f"skipping AcceptShiftSwapRequestStep as swap request {shift_swap_request_pk} does not exist")
            return

        try:
            shift_swap_request.take(self.user)
        except exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest:
            self.open_warning_window(payload, "A shift swap request cannot be created and taken by the same user")
            return
        except exceptions.ShiftSwapRequestNotOpenForTaking:
            self.open_warning_window(payload, "The shift swap request is not in a state which allows it to be taken")
            return

        self.update_message(shift_swap_request)


class ShiftSwapRequestFollowUp(scenario_step.ScenarioStep):
    @staticmethod
    def _generate_blocks(shift_swap_request: "ShiftSwapRequest") -> Block.AnyBlocks:
        # Time until shift swap starts (example: "14 days", "2 hours")
        delta = humanize.naturaldelta(timezone.now() - shift_swap_request.swap_start)

        return [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f":exclamation: This shift swap request is still open and will start in {delta}.\n"
                            "Jump back into the thread and accept it if you're available!"
                        ),
                    },
                },
            )
        ]

    def post_message(self, shift_swap_request: "ShiftSwapRequest") -> None:
        self._slack_client.api_call(
            "chat.postMessage",
            channel=shift_swap_request.slack_message.channel_id,
            thread_ts=shift_swap_request.slack_message.slack_id,
            reply_broadcast=True,
            blocks=self._generate_blocks(shift_swap_request),
        )


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": AcceptShiftSwapRequestStep.routing_uid(),
        "step": AcceptShiftSwapRequestStep,
    },
]
