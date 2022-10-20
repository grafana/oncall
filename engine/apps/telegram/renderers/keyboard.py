from enum import Enum
from typing import List, Optional, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from apps.alerts.models import AlertGroup
from apps.telegram.utils import CallbackQueryFactory


class Action(Enum):
    ACKNOWLEDGE = "acknowledge"
    UNACKNOWLEDGE = "unacknowledge"
    RESOLVE = "resolve"
    UNRESOLVE = "unresolve"
    SILENCE = "silence"
    UNSILENCE = "unsilence"


class TelegramKeyboardRenderer:
    def __init__(self, alert_group: AlertGroup):
        self.alert_group = alert_group

    # Inline keyboard with controls for alert group message
    def render_actions_keyboard(self) -> Optional[InlineKeyboardMarkup]:
        if self.alert_group.root_alert_group is not None:
            # No keyboard for attached incident
            return None

        rows = []

        # Acknowledge/Unacknowledge button
        if not self.alert_group.resolved:
            rows.append([self.acknowledge_button])

        # Resolve/Unresolve buttons
        rows.append([self.resolve_button])

        # Silence/Unsilence buttons
        if not self.alert_group.acknowledged and not self.alert_group.resolved:
            if not self.alert_group.silenced:
                rows.append(self.silence_buttons)
            else:
                rows.append([self.unsilence_button])

        return InlineKeyboardMarkup(rows)

    @staticmethod
    def render_link_to_channel_keyboard(link: str) -> InlineKeyboardMarkup:
        button = InlineKeyboardButton(text="Go to the incident", url=link)
        return InlineKeyboardMarkup([[button]])

    @property
    def acknowledge_button(self) -> InlineKeyboardButton:
        action = Action.ACKNOWLEDGE if not self.alert_group.acknowledged else Action.UNACKNOWLEDGE
        return self._render_button(text=action.value.capitalize(), action=action)

    @property
    def resolve_button(self) -> InlineKeyboardButton:
        action = Action.RESOLVE if not self.alert_group.resolved else Action.UNRESOLVE
        return self._render_button(text=action.value.capitalize(), action=action)

    @property
    def silence_buttons(self) -> List[InlineKeyboardButton]:
        silence_forever_button = self._render_button(text="🔕 forever", action=Action.SILENCE)

        silence_delay_one_hour = 3600  # one hour
        silence_one_hour_button = self._render_button(
            text="... for 1h", action=Action.SILENCE, action_data=silence_delay_one_hour
        )

        silence_delay_four_hours = 14400  # four hours
        silence_four_hours_button = self._render_button(
            text="... for 4h", action=Action.SILENCE, action_data=silence_delay_four_hours
        )

        return [silence_forever_button, silence_one_hour_button, silence_four_hours_button]

    @property
    def unsilence_button(self) -> InlineKeyboardButton:
        return self._render_button(text=Action.UNSILENCE.value.capitalize(), action=Action.UNSILENCE)

    def _render_button(self, text: str, action: Action, action_data: Optional[Union[int, str]] = None):
        callback_data_args = [self.alert_group.pk, action.value]
        if action_data is not None:
            callback_data_args.append(action_data)
        callback_data_args.append(f"x-oncall-org-id{self.alert_group.channel.organization.public_primary_key}")
        button = InlineKeyboardButton(text=text, callback_data=CallbackQueryFactory.encode_data(*callback_data_args))

        return button
