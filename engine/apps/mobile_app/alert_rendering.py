import typing

from emoji import emojize

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater, TemplatedAlert
from apps.alerts.models import AlertGroup
from common.utils import str_or_backup


def _validate_fcm_length_limit(value: typing.Optional[str]) -> str:
    """
    NOTE: technically FCM limits the data we send based on total # of bytes, not characters for title/subtitle. For now
    lets simply limit the title and subtitle to 200 characters and see how that goes with avoiding the `message is too big`
    FCM exception

    https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode
    """
    MAX_ALERT_TITLE_LENGTH = 200

    if value is None:
        return ""
    return f"{value[:MAX_ALERT_TITLE_LENGTH]}..." if len(value) > MAX_ALERT_TITLE_LENGTH else value


class AlertMobileAppTemplater(AlertTemplater):
    def _render_for(self):
        return "MOBILE_APP"

    def _postformat(self, templated_alert: TemplatedAlert) -> TemplatedAlert:
        templated_alert.title = _validate_fcm_length_limit(templated_alert.title)
        templated_alert.message = _validate_fcm_length_limit(templated_alert.message)
        return templated_alert


def _templatize_alert(alert_group: AlertGroup) -> TemplatedAlert:
    alert = alert_group.alerts.first()
    return AlertMobileAppTemplater(alert).render()


def get_push_notification_title(alert_group: AlertGroup, critical: bool) -> str:
    return _templatize_alert(alert_group).title or ("New Important Alert" if critical else "New Alert")


def get_push_notification_subtitle(alert_group: AlertGroup) -> str:
    templatized_subtitle = _templatize_alert(alert_group).message
    if templatized_subtitle:
        # only return the templatized subtitle if it resolves to something that is not None
        # otherwise fallback to the default
        return templatized_subtitle

    alert = alert_group.alerts.first()
    templated_alert = AlertMobileAppTemplater(alert).render()

    alert_title = _validate_fcm_length_limit(str_or_backup(templated_alert.title, "Alert Group"))

    status_verbose = "Firing"  # TODO: we should probably de-duplicate this text
    if alert_group.resolved:
        status_verbose = alert_group.get_resolve_text()
    elif alert_group.acknowledged:
        status_verbose = alert_group.get_acknowledge_text()

    number_of_alerts = alert_group.alerts.count()
    if number_of_alerts <= 10:
        alerts_count_str = str(number_of_alerts)
    else:
        alert_count_rounded = (number_of_alerts // 10) * 10
        alerts_count_str = f"{alert_count_rounded}+"

    alert_status = f"Status: {status_verbose}, alerts: {alerts_count_str}"

    subtitle = (
        f"#{alert_group.inside_organization_number} {alert_title}\n"
        + f"via {alert_group.channel.short_name}"
        + f"\n{alert_status}"
    )

    return emojize(subtitle, language="alias")
