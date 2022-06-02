from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import escape_html


class AlertTelegramTemplater(AlertTemplater):
    RENDER_FOR_TELEGRAM = "telegram"

    def _render_for(self):
        return self.RENDER_FOR_TELEGRAM

    def _preformat(self, data):
        return escape_html(self._slack_format_for_telegram(data))

    def _apply_preformatting(self):
        return True

    def _slack_format_for_telegram(self, data):
        sf = self.slack_formatter
        sf.channel_mention_format = "{}"
        sf.user_mention_format = "{}"
        sf.hyperlink_mention_format = "{title} - {url}"
        return sf.format(data)

    def _postformat(self, templated_alert):
        if templated_alert.title:
            templated_alert.title = self._slack_format_for_telegram(templated_alert.title)
        if templated_alert.message:
            templated_alert.message = self._slack_format_for_telegram(templated_alert.message)
        return templated_alert
