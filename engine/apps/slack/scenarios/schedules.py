import json
import typing

import pytz

from apps.schedules.models import OnCallSchedule
from apps.slack.scenarios import scenario_step
from apps.slack.types import (
    Block,
    BlockActionType,
    CompositionObjectOption,
    EventPayload,
    ModalView,
    PayloadType,
    ScenarioRoute,
)
from apps.slack.utils import format_datetime_to_slack_with_time
from common.insight_log import EntityEvent, write_resource_insight_log

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class EditScheduleShiftNotifyStep(scenario_step.ScenarioStep):
    notify_empty_oncall_options = {choice[0]: choice[1] for choice in OnCallSchedule.NotifyEmptyOnCall.choices}
    notify_oncall_shift_freq_options = {choice[0]: choice[1] for choice in OnCallSchedule.NotifyOnCallShiftFreq.choices}
    mention_oncall_start_options = {1: "Mention person in slack", 0: "Inform in channel without mention"}
    mention_oncall_next_options = {1: "Mention person in slack", 0: "Inform in channel without mention"}

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        if payload["actions"][0].get("value", None) and payload["actions"][0]["value"].startswith("edit"):
            self.open_settings_modal(payload)
        elif payload["actions"][0].get("type", None) and payload["actions"][0]["type"] == "static_select":
            self.set_selected_value(slack_user_identity, payload)

    def open_settings_modal(self, payload: EventPayload) -> None:
        schedule_id = payload["actions"][0]["value"].split("_")[1]
        try:
            _ = OnCallSchedule.objects.get(pk=schedule_id)  # noqa
        except OnCallSchedule.DoesNotExist:
            blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Schedule was removed"}}]
        else:
            blocks = self.get_modal_blocks(schedule_id)

        private_metadata = {}
        private_metadata["schedule_id"] = schedule_id

        view: ModalView = {
            "callback_id": EditScheduleShiftNotifyStep.routing_uid(),
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Notification preferences",
            },
            "private_metadata": json.dumps(private_metadata),
        }

        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )

    def set_selected_value(self, slack_user_identity: "SlackUserIdentity", payload: EventPayload) -> None:
        action = payload["actions"][0]
        private_metadata = json.loads(payload["view"]["private_metadata"])
        schedule_id = private_metadata["schedule_id"]
        schedule = OnCallSchedule.objects.get(pk=schedule_id)
        prev_state = schedule.insight_logs_serialized
        setattr(schedule, action["block_id"], int(action["selected_option"]["value"]))
        schedule.save()
        new_state = schedule.insight_logs_serialized
        write_resource_insight_log(
            instance=schedule,
            author=slack_user_identity.get_user(schedule.organization),
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def get_modal_blocks(self, schedule_id: str) -> typing.List[Block.Section]:
        blocks: typing.List[Block.Section] = [
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "Notification frequency"},
                "block_id": "notify_oncall_shift_freq",
                "accessory": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "----"},
                    "action_id": EditScheduleShiftNotifyStep.routing_uid(),
                    "options": self.get_options("notify_oncall_shift_freq"),
                    "initial_option": self.get_initial_option(schedule_id, "notify_oncall_shift_freq"),
                },
            },
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "Current shift notification settings"},
                "block_id": "mention_oncall_start",
                "accessory": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "----"},
                    "action_id": EditScheduleShiftNotifyStep.routing_uid(),
                    "options": self.get_options("mention_oncall_start"),
                    "initial_option": self.get_initial_option(schedule_id, "mention_oncall_start"),
                },
            },
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "Next shift notification settings"},
                "block_id": "mention_oncall_next",
                "accessory": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "----"},
                    "action_id": EditScheduleShiftNotifyStep.routing_uid(),
                    "options": self.get_options("mention_oncall_next"),
                    "initial_option": self.get_initial_option(schedule_id, "mention_oncall_next"),
                },
            },
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "Action for slot when no one is on-call"},
                "block_id": "notify_empty_oncall",
                "accessory": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "----"},
                    "action_id": EditScheduleShiftNotifyStep.routing_uid(),
                    "options": self.get_options("notify_empty_oncall"),
                    "initial_option": self.get_initial_option(schedule_id, "notify_empty_oncall"),
                },
            },
        ]

        return blocks

    def get_options(self, select_name: str) -> typing.List[CompositionObjectOption]:
        select_options = getattr(self, f"{select_name}_options")
        return [
            {"text": {"type": "plain_text", "text": select_options[option]}, "value": str(option)}
            for option in select_options
        ]

    def get_initial_option(self, schedule_id: str, select_name: str) -> CompositionObjectOption:
        schedule = OnCallSchedule.objects.get(pk=schedule_id)

        current_value = getattr(schedule, select_name)
        text = getattr(self, f"{select_name}_options")[current_value]

        initial_option: CompositionObjectOption = {
            "text": {
                "type": "plain_text",
                "text": f"{text}",
            },
            "value": str(int(current_value)),
        }

        return initial_option

    @classmethod
    def get_report_blocks_ical(cls, new_shifts, next_shifts, schedule: OnCallSchedule, empty: bool) -> Block.AnyBlocks:
        organization = schedule.organization
        if empty:
            if schedule.notify_empty_oncall == schedule.NotifyEmptyOnCall.ALL:
                now_text = "Inviting <!channel>. No one on-call now!\n"
            elif schedule.notify_empty_oncall == schedule.NotifyEmptyOnCall.PREV:
                user_ids: typing.List[str] = []
                for item in json.loads(schedule.current_shifts):
                    user_ids_from_shift = [u["pk"] for u in item.get("users", [])]
                    user_ids.extend(user_ids_from_shift)
                prev_users = organization.users.filter(public_primary_key__in=user_ids)
                users_verbal = "  ".join(
                    [f"{user.get_username_with_slack_verbal(mention=True)}" for user in prev_users]
                )
                now_text = f"No one on-call now! Inviting prev shift: {users_verbal}\n"
            else:
                now_text = "No one on-call now!\n"

        else:
            now_text = ""
            for shift in new_shifts:
                users = shift["users"]
                user_ids_from_shift = [u["pk"] for u in users]
                users = organization.users.filter(public_primary_key__in=user_ids_from_shift)
                now_text += cls.get_ical_shift_notification_text(shift, schedule.mention_oncall_start, users)
            now_text = "*New on-call shift:*\n" + now_text

        if len(next_shifts) == 0:
            if len(new_shifts) == 0:
                next_text = "No one on-call next hour!"
            else:
                next_text = "No one on-call next!"
        else:
            next_text = ""
            for shift in next_shifts:
                users = shift["users"]
                user_ids_from_shift = [u["pk"] for u in users]
                users = organization.users.filter(public_primary_key__in=user_ids_from_shift)
                next_text += cls.get_ical_shift_notification_text(shift, schedule.mention_oncall_next, users)
            next_text = "\n*Next on-call shift:*\n" + next_text

        text = f"{now_text}{next_text}"
        blocks: Block.AnyBlocks = [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                        "verbatim": True,
                    },
                },
            ),
            typing.cast(
                Block.Actions,
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": f"{cls.routing_uid()}",
                            "text": {"type": "plain_text", "text": ":gear:", "emoji": True},
                            "value": f"edit_{schedule.pk}",
                        },
                    ],
                },
            ),
            typing.cast(
                Block.Context,
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"On-call schedule *{schedule.name}*",
                        },
                    ],
                },
            ),
        ]
        return blocks

    @classmethod
    def get_ical_shift_notification_text(cls, shift, mention, users) -> str:
        notification = ""
        for user in users:
            if shift["all_day"]:
                user_notification = user.get_username_with_slack_verbal(mention=mention)
                if shift["start"].day == shift["end"].day:
                    all_day_text = shift["start"].strftime("%b %d")
                else:
                    all_day_text = f'From {shift["start"].strftime("%b %d")} to {shift["end"].strftime("%b %d")}'
                user_notification += f' {all_day_text} _All-day event in timezone "UTC"_\n'
            else:
                shift_start_timestamp = shift["start"].astimezone(pytz.UTC).timestamp()
                shift_end_timestamp = shift["end"].astimezone(pytz.UTC).timestamp()

                user_notification = (
                    user.get_username_with_slack_verbal(mention=mention)
                    + f" from {format_datetime_to_slack_with_time(shift_start_timestamp)}"
                    f" to {format_datetime_to_slack_with_time(shift_end_timestamp)}\n"
                )
            if not shift["is_override"]:
                priority = shift.get("priority_level", 0) or 0
                if priority != 0:
                    user_notification = f"[L{priority}] {user_notification}"
            notification += user_notification
        return notification


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": EditScheduleShiftNotifyStep.routing_uid(),
        "step": EditScheduleShiftNotifyStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": EditScheduleShiftNotifyStep.routing_uid(),
        "step": EditScheduleShiftNotifyStep,
    },
]
