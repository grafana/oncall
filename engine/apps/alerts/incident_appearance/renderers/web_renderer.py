from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertWebTemplater
from common.utils import str_or_backup


class AlertWebRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertWebTemplater

    def render(self):
        templated_alert = self.templated_alert
        return {
            "title": str_or_backup(templated_alert.title, "Alert"),
            "message": str_or_backup(templated_alert.message, ""),
            "image_url": str_or_backup(templated_alert.image_url, None),
            "source_link": str_or_backup(templated_alert.source_link, None),
        }


class AlertGroupWebRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group, alert=None):
        if alert is None:
            alert = alert_group.alerts.last()

        super().__init__(alert_group, alert)

    @property
    def alert_renderer_class(self):
        return AlertWebRenderer

    def render(self):
        return self.alert_renderer.render()
