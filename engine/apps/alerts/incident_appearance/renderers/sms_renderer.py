from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters import AlertSmsTemplater
from common.utils import str_or_backup


class AlertSmsRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertSmsTemplater


class AlertGroupSmsRenderer(AlertGroupBaseRenderer):
    @property
    def alert_renderer_class(self):
        return AlertSmsRenderer

    def render(self):
        templated_alert = self.alert_renderer.templated_alert
        title = str_or_backup(templated_alert.title, DEFAULT_BACKUP_TITLE)
        if self.alert_group.channel.organization.slack_team_identity and (
            permalink := self.alert_group.slack_permalink
        ):
            incident_link = permalink
        else:
            incident_link = self.alert_group.web_link
        return (
            f"You are invited to check an incident #{self.alert_group.inside_organization_number} with title "
            f'"{title}" in Grafana OnCall organization: "{self.alert_group.channel.organization.stack_slug}", '
            f"alert channel: {self.alert_group.channel.short_name}, "
            f"alerts registered: {self.alert_group.alerts.count()}, "
            f"{incident_link}\n"
            f"Your Grafana OnCall <3"
        )
