import typing

import humanize

from apps.alerts.incident_log_builder import IncidentLogBuilder

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup


class AlertGroupLogSlackRenderer:
    @staticmethod
    def render_incident_log_report_for_slack(alert_group: "AlertGroup"):
        from apps.alerts.models import AlertGroupLogRecord
        from apps.base.models import UserNotificationPolicyLogRecord

        log_builder = IncidentLogBuilder(alert_group)
        all_log_records = log_builder.get_log_records_list()

        attachments = []

        # get rendered logs
        result = ""
        for log_record in all_log_records:  # list of AlertGroupLogRecord and UserNotificationPolicyLogRecord logs
            if type(log_record) == AlertGroupLogRecord:
                result += f"{log_record.rendered_incident_log_line(for_slack=True)}\n"
            elif type(log_record) == UserNotificationPolicyLogRecord:
                result += f"{log_record.rendered_notification_log_line(for_slack=True)}\n"

        attachments.append(
            {
                "text": result,
            }
        )
        result = ""

        # check if escalation or invitation active
        if not (alert_group.resolved or alert_group.wiped_at or alert_group.root_alert_group):
            escalation_policies_plan = log_builder.get_incident_escalation_plan(for_slack=True)
            if escalation_policies_plan:
                result += "\n:arrow_down: :arrow_down: :arrow_down: Plan:\n\n"
                # humanize time, create plan text
                for time in sorted(escalation_policies_plan):
                    for plan_line in escalation_policies_plan[time]:
                        result += f"*{humanize.naturaldelta(time)}:* {plan_line}\n"

        if len(result) > 0:
            attachments.append(
                {
                    "text": result,
                }
            )
        return attachments
