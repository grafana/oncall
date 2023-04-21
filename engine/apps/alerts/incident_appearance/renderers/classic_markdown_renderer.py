from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertClassicMarkdownTemplater
from common.constants.alert_group_restrictions import IS_RESTRICTED_MESSAGE, IS_RESTRICTED_TITLE
from common.utils import str_or_backup


class AlertClassicMarkdownRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertClassicMarkdownTemplater

    def render(self):
        templated_alert = self.templated_alert
        is_restricted = self.alert.group.is_restricted

        return {
            "title": IS_RESTRICTED_TITLE if is_restricted else str_or_backup(templated_alert.title, "Alert"),
            "message": IS_RESTRICTED_MESSAGE if is_restricted else str_or_backup(templated_alert.message, ""),
            "image_url": None if is_restricted else str_or_backup(templated_alert.image_url, None),
            "source_link": None if is_restricted else str_or_backup(templated_alert.source_link, None),
        }


class AlertGroupClassicMarkdownRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group, alert=None):
        if alert is None:
            alert = alert_group.alerts.last()

        super().__init__(alert_group, alert)

    @property
    def alert_renderer_class(self):
        return AlertClassicMarkdownRenderer

    def render(self):
        return self.alert_renderer.render()
