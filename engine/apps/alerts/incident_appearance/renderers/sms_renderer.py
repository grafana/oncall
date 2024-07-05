from apps.alerts.incident_appearance.renderers.base_renderer import (
    AlertBaseRenderer,
    AlertGroupBaseRenderer,
    AlertGroupBundleBaseRenderer,
)
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
        return (
            f"Grafana OnCall: Alert group #{self.alert_group.inside_organization_number}"
            f'"{title}" from stack: "{self.alert_group.channel.organization.stack_slug}", '
            f"integration: {self.alert_group.channel.short_name}, "
            f"alerts registered: {self.alert_group.alerts.count()}."
        )


class AlertGroupBundleRenderer(AlertGroupBundleBaseRenderer):
    def render(self) -> str:
        alert_group_inside_organization_numbers = [
            alert_group.inside_organization_number for alert_group in self.alert_groups_to_render
        ]
        numbers_str = ", ".join(f"#{x}" for x in alert_group_inside_organization_numbers)

        other_alert_groups_count = self.alert_groups_count - len(self.alert_groups_to_render)
        if other_alert_groups_count > 0:
            numbers_str += f" and {other_alert_groups_count} more"

        channel_names = ", ".join([channel.short_name for channel in self.channels_to_render])
        if self.channels_count > 1:
            channel_names += f" and {self.channels_count - len(self.channels_to_render)} more"

        return (
            f"Grafana OnCall: Alert group(s) {numbers_str} "
            f"from stack: {self.channels_to_render[0].organization.stack_slug}, "
            f"integration(s): {channel_names}."
        )
