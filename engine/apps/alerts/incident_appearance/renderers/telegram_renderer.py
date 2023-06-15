from emoji import emojize

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters import AlertTelegramTemplater
from common.utils import str_or_backup


class AlertTelegramRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertTelegramTemplater


class AlertGroupTelegramRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group):
        super().__init__(alert_group)

        # render the last alert content as a Telegram message, so Telegram message is updated when a new alert comes
        self.alert_renderer = self.alert_renderer_class(self.alert_group.alerts.last())

    @property
    def alert_renderer_class(self):
        return AlertTelegramRenderer

    def render(self):
        templated_alert = self.alert_renderer.templated_alert
        title = str_or_backup(templated_alert.title, DEFAULT_BACKUP_TITLE)
        message = templated_alert.message
        image_url = templated_alert.image_url

        alerts_count = self.alert_group.alerts.count()
        if alerts_count <= 10:
            alerts_count_str = str(alerts_count)
        else:
            alert_count_rounded = (alerts_count // 10) * 10
            alerts_count_str = f"{alert_count_rounded}+"

        status_emoji = "🔴"
        if self.alert_group.resolved:
            status_emoji = "🟢"
        elif self.alert_group.acknowledged:
            status_emoji = "🟠"
        elif self.alert_group.silenced:
            status_emoji = "⚪️"  # white circle

        status_verbose = "Firing"  # TODO: we should probably de-duplicate this text
        if self.alert_group.resolved:
            status_verbose = self.alert_group.get_resolve_text()
        elif self.alert_group.acknowledged:
            status_verbose = self.alert_group.get_acknowledge_text()
        # First line in the invisible link with id of organization.
        # It is needed to add info about organization to the telegram message for the oncall-gateway.
        text = f"<a href='{self.alert_group.channel.organization.web_link_with_uuid}'>&#8205;</a>"
        text += f"{status_emoji} #{self.alert_group.inside_organization_number}, {title}\n"
        text += f"{status_verbose}, alerts: {alerts_count_str}\n"
        text += f"Source: {self.alert_group.channel.short_name}\n"
        text += f"{self.alert_group.web_link}"

        if message:
            text += f"\n\n{message}"

        if image_url is not None:
            text = f"<a href='{image_url}'>&#8205;</a>" + text

        return emojize(text, language="alias")
