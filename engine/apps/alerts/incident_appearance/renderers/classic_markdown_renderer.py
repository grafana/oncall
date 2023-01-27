from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertClassicMarkdownTemplater
from common.utils import str_or_backup


class AlertClassicMarkdownRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertClassicMarkdownTemplater

    def render(self, render_fields=["title", "message", "image_url", "source_link"]):
        templated_alert = self.templated_alert
        rendered_alert = {}
        if "title" in render_fields:
            rendered_alert["title"] = str_or_backup(templated_alert.title, "Alert")
        if "message" in render_fields:
            rendered_alert["message"] = str_or_backup(templated_alert.message, "")
        if "image_url" in render_fields:
            rendered_alert["image_url"] = str_or_backup(templated_alert.image_url, None)
        if "source_link" in render_fields:
            rendered_alert["source_link"] = str_or_backup(templated_alert.source_link, None)
        return rendered_alert


class AlertGroupClassicMarkdownRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group, alert=None):
        if alert is None:
            alert = alert_group.alerts.last()

        super().__init__(alert_group, alert)

    @property
    def alert_renderer_class(self):
        return AlertClassicMarkdownRenderer

    def render(self, *args, **kwargs):
        return self.alert_renderer.render(*args, **kwargs)
