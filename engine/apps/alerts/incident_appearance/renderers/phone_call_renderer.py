from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters import AlertPhoneCallTemplater
from common.utils import str_or_backup


class AlertPhoneCallRenderer(AlertBaseRenderer):
    @property
    def templater_class(self):
        return AlertPhoneCallTemplater


class AlertGroupPhoneCallRenderer(AlertGroupBaseRenderer):
    @property
    def alert_renderer_class(self):
        return AlertPhoneCallRenderer

    def render(self):
        templated_alert = self.alert_renderer.templated_alert
        title = str_or_backup(templated_alert.title, DEFAULT_BACKUP_TITLE)

        return title