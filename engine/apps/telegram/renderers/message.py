from apps.alerts.incident_appearance.renderers.telegram_renderer import (
    AlertGroupTelegramRenderer,
    AlertTelegramRenderer,
)
from apps.alerts.incident_log_builder import IncidentLogBuilder
from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.base.models import UserNotificationPolicyLogRecord
from apps.slack.slack_formatter import SlackFormatter
from common.utils import is_string_with_visible_characters

MAX_TELEGRAM_MESSAGE_LENGTH = 4096
MESSAGE_TRIMMED_TEXT = "\n\nMessage is trimmed! See full alert group here: {link}"


class TelegramMessageRenderer:
    def __init__(self, alert_group: AlertGroup):
        self.alert_group = alert_group

    def render_alert_group_message(self) -> str:
        text = AlertGroupTelegramRenderer(self.alert_group).render()

        if len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
            text = self._trim_text(text)

        return text

    def render_log_message(self, max_message_length: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> str:
        start_line_text = "Alert group log:\n"

        slack_formatter = SlackFormatter(self.alert_group.channel.organization)
        log_builder = IncidentLogBuilder(alert_group=self.alert_group)
        log_records = log_builder.get_log_records_list()

        log_lines = []
        for log_record in log_records:
            if isinstance(log_record, AlertGroupLogRecord):
                log_line = log_record.rendered_incident_log_line(html=True)

                # dirty hack to deal with attach / unattach logs
                log_line = slack_formatter.render_text(log_line, process_markdown=True)
                log_line = log_line.replace("<p>", "").replace("</p>", "")

                log_lines.append(log_line)
            elif isinstance(log_record, UserNotificationPolicyLogRecord):
                log_line = log_record.rendered_notification_log_line(html=True)
                log_lines.append(log_line)

        message_trimmed_text = MESSAGE_TRIMMED_TEXT.format(link=self.alert_group.web_link)
        max_log_lines_length = max_message_length - len(start_line_text) - len(message_trimmed_text)
        if max_log_lines_length < 0:
            return ""
        is_message_trimmed = len("\n".join(log_lines)) > max_log_lines_length
        while len("\n".join(log_lines)) > max_log_lines_length:
            log_lines.pop()

        log_lines_text = "\n".join(log_lines)
        if is_message_trimmed:
            log_lines_text += message_trimmed_text

        text = start_line_text + log_lines_text
        return text

    def render_actions_message(self) -> str:
        if self.alert_group.root_alert_group is None:
            text = "Actions available for this alert group"
        else:
            # No actions for attached alert group
            text = "No actions are available for this alert group"

        return text

    def render_personal_message(self):
        text = AlertGroupTelegramRenderer(self.alert_group).render()

        if len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
            return self._trim_text(text)

        text += "\n" * 3 + self.render_log_message(max_message_length=MAX_TELEGRAM_MESSAGE_LENGTH - len(text))
        return text

    def render_link_to_channel_message(self, include_title: bool = True) -> str:
        text = "👀 You are invited to look at an alert group!"

        if include_title:
            first_alert_in_group = self.alert_group.alerts.first()
            templated_alert = AlertTelegramRenderer(first_alert_in_group).templated_alert
            if is_string_with_visible_characters(templated_alert.title):
                text += f"\n<b>#{self.alert_group.inside_organization_number}, {templated_alert.title}</b>"

        return text

    def render_formatting_error_message(self) -> str:
        return (
            "You have a new alert group, but Telegram can't render its content! "
            f"Please check it out: {self.alert_group.web_link}"
        )

    def _trim_text(self, text: str) -> str:
        trim_fallback_text = MESSAGE_TRIMMED_TEXT.format(link=self.alert_group.web_link)
        text = text[: MAX_TELEGRAM_MESSAGE_LENGTH - len(trim_fallback_text)] + trim_fallback_text
        return text
