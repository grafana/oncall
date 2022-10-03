import humanize

from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.templaters.alert_templater import AlertTemplater
from apps.alerts.incident_log_builder import IncidentLogBuilder
from common.utils import str_or_backup


class AlertMattermostTemplater(AlertTemplater):
    RENDER_FOR_MATTERMOST = "mattermost"  # needs to match the backend id!

    def _render_for(self):
        return self.RENDER_FOR_MATTERMOST

    # preformat/posformat


def get_templated_fields(alert_group):
    """Return title and content for the alert notification."""
    alert = alert_group.alerts.last()

    templated_alert = AlertMattermostTemplater(alert).render()
    title = str_or_backup(templated_alert.title, DEFAULT_BACKUP_TITLE)
    body = templated_alert.message or ""

    # TODO: update to match mattermost messages rendering

    status_emoji = "🔴"
    if alert_group.resolved:
        status_emoji = "🟢"
    elif alert_group.acknowledged:
        status_emoji = "🟠"
    elif alert_group.silenced:
        status_emoji = "⚪️"  # white circle

    status_verbose = "Alerting"
    if alert_group.resolved:
        status_verbose = alert_group.get_resolve_text()
    elif alert_group.acknowledged:
        status_verbose = alert_group.get_acknowledge_text()
    elif alert_group.silenced:
        status_verbose = "Silenced"

    message = f"{status_emoji} {status_verbose}\n{body}"

    return title, message


def build_log_message(alert_group):
    """Return title and content for the incident log notification."""
    from apps.alerts.models import AlertGroupLogRecord
    from apps.base.models import UserNotificationPolicyLogRecord

    log_builder = IncidentLogBuilder(alert_group=alert_group)
    log_records = log_builder.get_log_records_list()

    alert = alert_group.alerts.last()
    templated_alert = AlertMattermostTemplater(alert).render()
    title = f"{templated_alert.title} / log"

    # TODO: update to match mattermost messages rendering

    # incident log
    message = ""
    for log_record in log_records:
        if isinstance(log_record, AlertGroupLogRecord):
            log_line = log_record.rendered_incident_log_line()
            message += "\n" + log_line
        elif isinstance(log_record, UserNotificationPolicyLogRecord):
            log_line = log_record.rendered_notification_log_line()
            message += "\n" + log_line

    # alert plan
    if not (alert_group.resolved or alert_group.is_archived or alert_group.wiped_at or alert_group.root_alert_group):
        escalation_policies_plan = log_builder.get_incident_escalation_plan(for_slack=False)
        message += "\n---------------\n"
        for time in sorted(escalation_policies_plan):
            for plan_line in escalation_policies_plan[time]:
                message += f"*{humanize.naturaldelta(time)}:* {plan_line}"

    return title, message
