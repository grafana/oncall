from emoji import emojize

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import str_or_backup


class AlertMobileAppTemplater(AlertTemplater):
    def _render_for(self):
        return "MOBILE_APP"


def get_push_notification_subtitle(alert_group):
    alert = alert_group.alerts.first()
    templated_alert = AlertMobileAppTemplater(alert).render()
    alert_title = str_or_backup(templated_alert.title, "Alert Group")

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
