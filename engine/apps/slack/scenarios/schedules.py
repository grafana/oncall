import json
import typing

import pytz

from apps.schedules.models import OnCallSchedule
from apps.slack.chatops_proxy_routing import make_value
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
from apps.slack.utils import SlackDateFormat, format_datetime_to_slack_with_time
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
        action_type = payload["actions"][0]["type"]
        if action_type == BlockActionType.BUTTON:
            self.open_settings_modal(payload)
        elif action_type == BlockActionType.STATIC_SELECT:
            self.set_selected_value(slack_user_identity, payload)

    def open_settings_modal(self, payload: EventPayload) -> None:
        value = payload["actions"][0]["value"]
        try:
            schedule_id = json.loads(value)["schedule_id"]
        except json.JSONDecodeError:
            # Deprecated and kept for backward compatibility (so older Slack messages can still be processed)
            schedule_id = value.split("_")[1]

        try:
            schedule = OnCallSchedule.objects.get(pk=schedule_id)  # noqa
        except OnCallSchedule.DoesNotExist:
            blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Schedule was removed"}}]
        else:
            blocks = self.get_modal_blocks(schedule)

        view: ModalView = {
            "callback_id": EditScheduleShiftNotifyStep.routing_uid(),
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Notification preferences",
            },
            "private_metadata": json.dumps({"schedule_id": schedule_id}),
        }

        self._slack_client.views_open(trigger_id=payload["trigger_id"], view=view)

    def set_selected_value(self, slack_user_identity: "SlackUserIdentity", payload: EventPayload) -> None:
        action = payload["actions"][0]
        private_metadata = json.loads(payload["view"]["private_metadata"])
        schedule_id = private_metadata["schedule_id"]
        schedule = OnCallSchedule.objects.get(pk=schedule_id)
        prev_state = schedule.insight_logs_serialized
        setattr(schedule, action["block_id"], json.loads(action["selected_option"]["value"])["option"])
        schedule.save()
        new_state = schedule.insight_logs_serialized
        write_resource_insight_log(
            instance=schedule,
            author=slack_user_identity.get_user(schedule.organization),
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def get_modal_blocks(self, schedule: OnCallSchedule) -> typing.List[Block.Section]:
        blocks: typing.List[Block.Section] = [
            {
                "type": "section",
                "text": {"type": "plain_text", "text": "Notification frequency"},
                "block_id": "notify_oncall_shift_freq",
                "accessory": {
                    "type": "static_select",
                    "placeholder": {"type": "plain_text", "text": "----"},
                    "action_id": EditScheduleShiftNotifyStep.routing_uid(),
                    "options": self.get_options(schedule, "notify_oncall_shift_freq"),
                    "initial_option": self.get_initial_option(schedule, "notify_oncall_shift_freq"),
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
                    "options": self.get_options(schedule, "mention_oncall_start"),
                    "initial_option": self.get_initial_option(schedule, "mention_oncall_start"),
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
                    "options": self.get_options(schedule, "mention_oncall_next"),
                    "initial_option": self.get_initial_option(schedule, "mention_oncall_next"),
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
                    "options": self.get_options(schedule, "notify_empty_oncall"),
                    "initial_option": self.get_initial_option(schedule, "notify_empty_oncall"),
                },
            },
        ]

        return blocks

    def get_options(self, schedule: OnCallSchedule, select_name: str) -> typing.List[CompositionObjectOption]:
        select_options = getattr(self, f"{select_name}_options")
        return [
            {
                "text": {"type": "plain_text", "text": select_options[option]},
                "value": make_value({"option": option}, schedule.organization),
            }
            for option in select_options
        ]

    def get_initial_option(self, schedule: OnCallSchedule, select_name: str) -> CompositionObjectOption:
        current_value = getattr(schedule, select_name)
        text = getattr(self, f"{select_name}_options")[current_value]

        initial_option: CompositionObjectOption = {
            "text": {
                "type": "plain_text",
                "text": f"{text}",
            },
            "value": make_value({"option": int(current_value)}, schedule.organization),
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

            now_text = "*New on-call shift*\n" + now_text

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
            next_text = "\n*Next on-call shift*\n" + next_text

        blocks: Block.AnyBlocks = [
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"On-call shifts update for schedule *<{schedule.web_detail_page_link}|{schedule.name}>*",
                        "verbatim": True,
                    },
                },
            ),
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": now_text,
                        "verbatim": True,
                    },
                },
            ),
            typing.cast(
                Block.Section,
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": next_text,
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
                            "value": make_value({"schedule_id": schedule.pk}, schedule.organization),
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
                user_notification = user.get_username_with_slack_verbal(mention=mention) + "\n"
                if shift["start"].day == shift["end"].day:
                    all_day_text = shift["start"].strftime("%b %d")
                else:
                    all_day_text = f'{shift["start"].strftime("%b %d")} - {shift["end"].strftime("%b %d")}'
                user_notification += f' {all_day_text} _All-day event in timezone "UTC"_\n'
            else:
                shift_start_timestamp = shift["start"].astimezone(pytz.UTC).timestamp()
                shift_end_timestamp = shift["end"].astimezone(pytz.UTC).timestamp()

                start_timestamp = format_datetime_to_slack_with_time(shift_start_timestamp, SlackDateFormat.DATE_LONG)
                end_timestamp = format_datetime_to_slack_with_time(shift_end_timestamp, SlackDateFormat.DATE_LONG)
                user_notification = (
                    user.get_username_with_slack_verbal(mention=mention) + f"\n{start_timestamp} - {end_timestamp}\n"
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
