import json

import pytz
from django.utils import timezone

from apps.schedules.models import OnCallSchedule
from apps.slack.scenarios import scenario_step
from apps.slack.utils import format_datetime_to_slack
from common.insight_log import EntityEvent, write_resource_insight_log


class EditScheduleShiftNotifyStep(scenario_step.ScenarioStep):
    notify_empty_oncall_options = {choice[0]: choice[1] for choice in OnCallSchedule.NotifyEmptyOnCall.choices}
    notify_oncall_shift_freq_options = {choice[0]: choice[1] for choice in OnCallSchedule.NotifyOnCallShiftFreq.choices}
    mention_oncall_start_options = {1: "Mention person in slack", 0: "Inform in channel without mention"}
    mention_oncall_next_options = {1: "Mention person in slack", 0: "Inform in channel without mention"}

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        if payload["actions"][0].get("value", None) and payload["actions"][0]["value"].startswith("edit"):
            self.open_settings_modal(payload)
        elif payload["actions"][0].get("type", None) and payload["actions"][0]["type"] == "static_select":
            self.set_selected_value(slack_user_identity, payload)

    def open_settings_modal(self, payload, schedule_id=None):
        schedule_id = payload["actions"][0]["value"].split("_")[1] if schedule_id is None else schedule_id
        try:
            _ = OnCallSchedule.objects.get(pk=schedule_id)  # noqa
        except OnCallSchedule.DoesNotExist:
            blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Schedule was removed"}}]
        else:
            blocks = self.get_modal_blocks(schedule_id)

        private_metadata = {}
        private_metadata["schedule_id"] = schedule_id

        view = {
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

    def set_selected_value(self, slack_user_identity, payload):
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

    def get_modal_blocks(self, schedule_id):
        blocks = [
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

    def get_options(self, select_name):
        select_options = getattr(self, f"{select_name}_options")
        return [
            {"text": {"type": "plain_text", "text": select_options[option]}, "value": str(option)}
            for option in select_options
        ]

    def get_initial_option(self, schedule_id, select_name):

        schedule = OnCallSchedule.objects.get(pk=schedule_id)

        current_value = getattr(schedule, select_name)
        text = getattr(self, f"{select_name}_options")[current_value]

        initial_option = {
            "text": {
                "type": "plain_text",
                "text": f"{text}",
            },
            "value": str(int(current_value)),
        }

        return initial_option

    @classmethod
    def get_report_blocks_ical(cls, new_shifts, next_shifts, schedule, empty):
        organization = schedule.organization
        if empty:
            if schedule.notify_empty_oncall == schedule.NotifyEmptyOnCall.ALL:
                now_text = "Inviting <!channel>. No one on-call now!\n"
            elif schedule.notify_empty_oncall == schedule.NotifyEmptyOnCall.PREV:
                user_ids = []
                for item in json.loads(schedule.current_shifts).values():
                    user_ids.extend(item.get("users", []))
                prev_users = organization.users.filter(id__in=user_ids)
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
                next_text += cls.get_ical_shift_notification_text(shift, schedule.mention_oncall_next, users)
            next_text = "\n*Next on-call shift:*\n" + next_text

        text = f"{now_text}{next_text}"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                    "verbatim": True,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": f"{cls.routing_uid()}",
                        "text": {"type": "plain_text", "text": ":gear:", "emoji": True},
                        "value": f"edit_{schedule.pk}",
                    }
                ],
            },
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"On-call schedule *{schedule.name}*"}]},
        ]
        return blocks

    @classmethod
    def get_report_blocks_manual(cls, current_shift, next_shift, schedule):

        current_piece, current_user = current_shift

        start_day = timezone.datetime.now()
        current_hour = timezone.datetime.today().hour
        start_hour = current_piece.starts_at.hour
        if start_hour > current_hour:
            start_day -= timezone.timedelta(days=1)

        shift_start = start_day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        shift_end = shift_start + timezone.timedelta(hours=12)
        shift_start_timestamp = int(shift_start.astimezone(pytz.UTC).timestamp())
        shift_end_timestamp = int(shift_end.astimezone(pytz.UTC).timestamp())

        next_shift_end = shift_end + timezone.timedelta(hours=12)
        next_shift_end_timestamp = int(next_shift_end.astimezone(pytz.UTC).timestamp())

        now_text = "_*Now*_:\n"
        if schedule.mention_oncall_start:
            user_mention = current_user.get_username_with_slack_verbal(
                mention=True,
            )

        else:
            user_mention = current_user.get_username_with_slack_verbal(
                mention=False,
            )
        now_text += f"*{user_mention}*"

        now_text += f" from {format_datetime_to_slack(shift_start_timestamp)}"
        now_text += f" to {format_datetime_to_slack(shift_end_timestamp)}"

        next_piece, next_user = next_shift
        next_text = "\n_*Next*_:\n"
        if schedule.mention_oncall_next:
            user_mention = next_user.get_username_with_slack_verbal(
                mention=True,
            )
        else:
            user_mention = next_user.get_username_with_slack_verbal(
                mention=False,
            )
        next_text += f"*{user_mention}*"

        next_text += f" from {format_datetime_to_slack(shift_end_timestamp)}"
        next_text += f" to {format_datetime_to_slack(next_shift_end_timestamp)}"

        text = f"{now_text}{next_text}"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                    "verbatim": True,
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": f"{cls.routing_uid()}",
                        "text": {"type": "plain_text", "text": ":gear:", "emoji": True},
                        "value": f"edit_{schedule.pk}",
                    }
                ],
            },
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"On-call schedule *{schedule.name}*"}]},
        ]

        return blocks

    @classmethod
    def get_ical_shift_notification_text(cls, shift, mention, users):

        if shift["all_day"]:
            notification = " ".join([f"{user.get_username_with_slack_verbal(mention=mention)}" for user in users])
            user_verbal = shift["users"][0].get_username_with_slack_verbal(
                mention=False,
            )
            if shift["start"].day == shift["end"].day:
                all_day_text = shift["start"].strftime("%b %d")
            else:
                all_day_text = f'From {shift["start"].strftime("%b %d")} to {shift["end"].strftime("%b %d")}'
            notification += (
                f" {all_day_text} _All-day event in *{user_verbal}'s* timezone_ " f'- {shift["users"][0].timezone}.\n'
            )
        else:
            shift_start_timestamp = int(shift["start"].astimezone(pytz.UTC).timestamp())
            shift_end_timestamp = int(shift["end"].astimezone(pytz.UTC).timestamp())

            notification = (
                " ".join([f"{user.get_username_with_slack_verbal(mention=mention)}" for user in users])
                + f" from {format_datetime_to_slack(shift_start_timestamp)}"
                f" to {format_datetime_to_slack(shift_end_timestamp)}\n"
            )
        priority = shift.get("priority", 0) - shift.get("priority_increased_by", 0)
        if priority != 0:
            notification = f"[L{shift.get('priority')}] {notification}"
        return notification


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": EditScheduleShiftNotifyStep.routing_uid(),
        "step": EditScheduleShiftNotifyStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": EditScheduleShiftNotifyStep.routing_uid(),
        "step": EditScheduleShiftNotifyStep,
    },
]
