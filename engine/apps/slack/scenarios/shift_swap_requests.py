import json
import logging
import typing

from apps.slack.models import SlackMessage
from apps.slack.scenarios import scenario_step
from apps.slack.types import Block, BlockActionType, EventPayload, PayloadType, RoutingSteps

if typing.TYPE_CHECKING:
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SHIFT_SWAP_PK_ACTION_KEY = "shift_swap_request_pk"


class BaseShiftSwapRequestStep:
    def _generate_blocks(self, shift_swap_request: "ShiftSwapRequest") -> typing.List[Block.Any]:
        pk = shift_swap_request.pk
        request_is_taken = shift_swap_request.status == shift_swap_request.Statuses.TAKEN

        # TODO: come up with a better layout for this..
        main_message_text = f"Your teammate {shift_swap_request.beneficiary.get_username_with_slack_verbal()} has submitted a shift swap request."

        if request_is_taken:
            main_message_text += "Update. This request has been fulfilled!"

        blocks: typing.List[Block.Any] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": main_message_text,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    # TODO: I believe it'll be easier to wait to generate this until we have the schedule override changes in place
                    # NOTE: use apps.slack.utils.format_datetime_to_slack method to format the datetimes
                    "text": "*📅 Shift Details*: 9h00 - 17h00 (UTC) daily from Monday July 24, 2023 - July 28, 2023",
                },
            },
        ]

        if description := shift_swap_request.description:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📝 Description*: {description}",
                    },
                }
            )

        if not request_is_taken:
            value = {
                SHIFT_SWAP_PK_ACTION_KEY: pk,
                "organization_id": shift_swap_request.organization.pk,
            }

            blocks.append(
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
                }
            )

        blocks.extend(
            [
                {
                    "type": "divider",
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"👀 View the shift swap within Grafana OnCall by clicking <{shift_swap_request.web_link}|here>.",
                        },
                    ],
                },
            ]
        )

        return blocks


class AcceptShiftSwapRequestStep(BaseShiftSwapRequestStep, scenario_step.ScenarioStep):
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

        blocks = self._generate_blocks(shift_swap_request)

        # TODO: better error handling here...
        self._slack_client.api_call(
            "chat.update",
            channel=shift_swap_request.slack_channel_id,
            ts=shift_swap_request.slack_message.slack_id,
            blocks=blocks,
        )


class ShiftSwapRequestCreationStep(BaseShiftSwapRequestStep, scenario_step.ScenarioStep):
    def send_creation_message(self, shift_swap_request: "ShiftSwapRequest") -> None:
        pk = shift_swap_request.pk
        channel_id = shift_swap_request.slack_channel_id
        organization = self.organization

        if channel_id is None:
            logger.info(f"Skipping posting message to Slack for shift_swap_request {pk} because channel_id is None")
            return

        blocks = self._generate_blocks(shift_swap_request)
        result = self._slack_client.api_call("chat.postMessage", channel=channel_id, blocks=blocks)

        slack_message = SlackMessage.objects.create(
            slack_id=result["ts"],
            organization=organization,
            _slack_team_identity=self.slack_team_identity,
            channel_id=channel_id,
        )

        shift_swap_request.slack_message = slack_message
        shift_swap_request.save(update_fields=["slack_message"])

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        pass


STEPS_ROUTING: RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": AcceptShiftSwapRequestStep.routing_uid(),
        "step": AcceptShiftSwapRequestStep,
    },
]
