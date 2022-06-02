from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import clean_markup


class AlertSmsTemplater(AlertTemplater):
    RENDER_FOR_SMS = "sms"

    def _render_for(self):
        return self.RENDER_FOR_SMS

    def _clean_markup(self, data):
        return clean_markup(data)

    def _postformat(self, templated_alert):
        templated_alert.title = self._postformat_pipeline(templated_alert.title)
        templated_alert.message = self._postformat_pipeline(templated_alert.message)
        return templated_alert

    def _postformat_pipeline(self, text):
        return clean_markup(self._slack_format_for_sms(text)) if text is not None else text

    def _slack_format_for_sms(self, data):
        sf = self.slack_formatter
        sf.user_mention_format = "{}"
        sf.channel_mention_format = "#{}"
        sf.hyperlink_mention_format = "{title}"
        return sf.format(data)
