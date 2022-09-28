from django.template.loader import render_to_string

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters import AlertEmailTemplater
from common.utils import str_or_backup


class AlertEmailRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertEmailTemplater


class AlertGroupEmailRenderer(AlertGroupBaseRenderer):
    @property
    def alert_renderer_class(self):
        return AlertEmailRenderer

    def render(self, limit_notification=False):
        subject = "You are invited to check an incident from Grafana OnCall"
        templated_alert = self.alert_renderer.templated_alert

        title_fallback = (
            f"#{self.alert_group.inside_organization_number} "
            f"{DEFAULT_BACKUP_TITLE} via {self.alert_group.channel.verbal_name}"
        )

        content = render_to_string(
            "email_notification.html",
            {
                "url": self.alert_group.slack_permalink or self.alert_group.web_link,
                "title": str_or_backup(templated_alert.title, title_fallback),
                "message": str_or_backup(templated_alert.message, ""),  # not render message it all if smth go wrong
                "amixr_team": self.alert_group.channel.organization,
                "alert_channel": self.alert_group.channel.short_name,
                "limit_notification": limit_notification,
                "emails_left": self.alert_group.channel.organization.emails_left,
            },
        )

        return subject, content
