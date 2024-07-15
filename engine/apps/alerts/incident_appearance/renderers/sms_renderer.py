from django.db.models import Count

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


class AlertGroupSMSBundleRenderer(AlertGroupBundleBaseRenderer):
    def render(self) -> str:
        """
        Renders SMS message for notification bundle: gets total count of unique alert groups and alert receive channels
        in the bundle, renders text with `inside_organization_number` of 3 alert groups (MAX_ALERT_GROUPS_TO_RENDER) and
        `short_name` of 1 alert receive channel (MAX_CHANNELS_TO_RENDER). If there are more unique alert groups / alert
        receive channels to notify about, adds "and X more" to the SMS message
        """

        channels_and_alert_groups_count = self.notifications.aggregate(
            channels_count=Count("alert_receive_channel", distinct=True),
            alert_groups_count=Count("alert_group", distinct=True),
        )
        alert_groups_count = channels_and_alert_groups_count["alert_groups_count"]
        channels_count = channels_and_alert_groups_count["channels_count"]

        # get 3 unique alert groups from notifications
        alert_groups_to_render = []
        for notification in self.notifications:
            if notification.alert_group not in alert_groups_to_render:
                alert_groups_to_render.append(notification.alert_group)
                if len(alert_groups_to_render) == self.MAX_ALERT_GROUPS_TO_RENDER:
                    break
        # render text for alert groups
        alert_group_inside_organization_numbers = [
            alert_group.inside_organization_number for alert_group in alert_groups_to_render
        ]
        numbers_str = ", ".join(f"#{x}" for x in alert_group_inside_organization_numbers)
        alert_groups_text = "Alert groups " if alert_groups_count > 1 else "Alert group "
        alert_groups_text += numbers_str

        if alert_groups_count > self.MAX_ALERT_GROUPS_TO_RENDER:
            alert_groups_text += f" and {alert_groups_count - self.MAX_ALERT_GROUPS_TO_RENDER} more"

        # render text for alert receive channels
        channels_to_render = [alert_groups_to_render[i].channel for i in range(self.MAX_CHANNELS_TO_RENDER)]
        channel_names = ", ".join([channel.short_name for channel in channels_to_render])
        channels_text = "integrations: " if channels_count > 1 else "integration: "
        channels_text += channel_names

        if channels_count > self.MAX_CHANNELS_TO_RENDER:
            channels_text += f" and {channels_count - self.MAX_CHANNELS_TO_RENDER} more"

        return (
            f"Grafana OnCall: {alert_groups_text} "
            f"from stack: {channels_to_render[0].organization.stack_slug}, "
            f"{channels_text}."
        )
