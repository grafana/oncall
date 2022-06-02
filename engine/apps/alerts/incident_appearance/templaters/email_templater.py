from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater


class AlertEmailTemplater(AlertTemplater):
    RENDER_FOR_EMAIL = "email"

    def _render_for(self):
        return self.RENDER_FOR_EMAIL

    def _postformat(self, templated_alert):
        templated_alert.title = self._slack_format_for_email(templated_alert.title)
        templated_alert.message = self._slack_format_for_email(templated_alert.message)
        return templated_alert

    def _slack_format_for_email(self, data):
        sf = self.slack_formatter
        sf.hyperlink_mention_format = "{title} - {url}"
        return sf.format(data)
