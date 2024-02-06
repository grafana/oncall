import typing

from emoji import emojize

from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from apps.alerts.models import AlertGroup
from apps.labels.alert_group_labels import gather_labels_from_alert_receive_channel_and_raw_request_data
from common.jinja_templater.apply_jinja_template import (
    JinjaTemplateError,
    JinjaTemplateWarning,
    apply_jinja_template_to_alert_payload_and_labels,
)
from common.utils import str_or_backup

MAX_ALERT_TITLE_LENGTH = 200
"""
NOTE: technically FCM limits the data we send based on total # of bytes, not characters for title/subtitle. For now
lets simply limit the title and subtitle to 200 characters and see how that goes with avoiding the `message is too big`
FCM exception

https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode
"""


class AlertMobileAppTemplater(AlertTemplater):
    def _render_for(self):
        return "MOBILE_APP"


def _templatize_alert(
    alert_group: AlertGroup,
    integration_attribute: typing.Literal["mobile_app_title_template", "mobile_app_message_template"],
) -> typing.Optional[str]:
    alert = alert_group.alerts.first()
    alert_receive_channel = alert_group.channel
    alert_payload = alert.raw_request_data

    parsed_labels = gather_labels_from_alert_receive_channel_and_raw_request_data(alert_receive_channel, alert_payload)

    try:
        return apply_jinja_template_to_alert_payload_and_labels(
            getattr(alert_receive_channel, integration_attribute),
            alert.raw_request_data,
            parsed_labels,
            result_length_limit=MAX_ALERT_TITLE_LENGTH,
        )
    except (JinjaTemplateError, JinjaTemplateWarning):
        return None


def get_push_notification_title(alert_group: AlertGroup, critical: bool) -> str:
    def _determine_title() -> str:
        return "New Important Alert" if critical else "New Alert"

    if not alert_group.channel.mobile_app_title_template:
        return _determine_title()

    return _templatize_alert(alert_group, "mobile_app_title_template") or _determine_title()


def get_push_notification_subtitle(alert_group: AlertGroup) -> str:
    if alert_group.channel.mobile_app_message_template is not None:
        # only return the templatized subtitle if it resolves to something that is not None
        # otherwise fallback to the default
        templatized_subtitle = _templatize_alert(alert_group, "mobile_app_message_template")

        if templatized_subtitle:
            return templatized_subtitle

    alert = alert_group.alerts.first()
    templated_alert = AlertMobileAppTemplater(alert).render()

    alert_title = str_or_backup(templated_alert.title, "Alert Group")
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
