from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater


class AlertClassicMarkdownTemplater(AlertTemplater):
    RENDER_FOR = "web"

    def _render_for(self):
        return self.RENDER_FOR

    def _postformat(self, templated_alert):
        if templated_alert.title:
            templated_alert.title = self._slack_format(templated_alert.title)
        if templated_alert.message:
            templated_alert.message = self._slack_format(templated_alert.message)
        return templated_alert

    def _slack_format(self, data):
        sf = self.slack_formatter
        sf.hyperlink_mention_format = "[{title}]({url})"
        return sf.format(data)
