from emoji import emojize

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from common.utils import str_or_backup


class AlertMobileAppTemplater(AlertTemplater):
    def _render_for(self):
        return "MOBILE_APP"


def get_push_notification_subtitle(alert_group):
    MAX_ALERT_TITLE_LENGTH = 200
    print(f"ALERTS COUNT: {alert_group.alerts.count}")  # TODO: debugging test. remove after debugging
    alert = alert_group.alerts.first()
    print(f"ALERT TITLE: {alert.title}, DATA: {alert.raw_request_data}")  # TODO: debugging test. remove after debugging
    templated_alert = AlertMobileAppTemplater(alert).render()
    print(f"TEMPLATED ALERT: {templated_alert}")  # TODO: debugging test. remove after debugging
    alert_title = str_or_backup(templated_alert.title, "Alert Group")
    # limit alert title length to prevent FCM `message is too big` exception
    # https://firebase.google.com/docs/cloud-messaging/concept-options#notifications_and_data_messages
    if len(alert_title) > MAX_ALERT_TITLE_LENGTH:
        alert_title = f"{alert_title[:MAX_ALERT_TITLE_LENGTH]}..."

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
