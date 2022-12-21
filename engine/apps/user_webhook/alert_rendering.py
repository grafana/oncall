from apps.alerts.incident_appearance.templaters import AlertWebTemplater


class AlertUserWebhookTemplater(AlertWebTemplater):
    def _render_for(self):
        return "USER_WEBHOOK"


def build_title_and_message(alert_group):
    alert = alert_group.alerts.first()
    templated_alert = AlertUserWebhookTemplater(alert).render()
    title = templated_alert.title
    message = templated_alert.message
    return title, message
