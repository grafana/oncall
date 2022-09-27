from apps.alerts.signals import (
    alert_create_signal,
    alert_group_action_triggered_signal,
    alert_group_update_log_report_signal,
)

from .listeners import on_action_triggered, on_alert_created, on_update_log_report

alert_create_signal.connect(on_alert_created)
alert_group_action_triggered_signal.connect(on_action_triggered)
alert_group_update_log_report_signal.connect(on_update_log_report)
