from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater


class AlertSlackTemplater(AlertTemplater):
    RENDER_FOR_SLACK = "slack"

    def _render_for(self):
        return self.RENDER_FOR_SLACK

    def _postformat(self, templated_alert):
        # We need to replace new line characters in slack title because slack markdown would break on multiline titles
        if templated_alert.title:
            templated_alert.title = templated_alert.title.replace("\n", "").replace("\r", "")
        return templated_alert
