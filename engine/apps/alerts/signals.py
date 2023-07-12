import django.dispatch

from apps.slack.representatives.alert_group_representative import AlertGroupSlackRepresentative
from apps.slack.representatives.user_representative import UserSlackRepresentative

"""
There are three entities which require sync between web, slack and telegram.
AlertGroup, AlertGroup's logs and AlertGroup's resolution notes.
"""
# Signal to create alert group message in all connected integrations (Slack, Telegram)
alert_create_signal = django.dispatch.Signal()

alert_group_created_signal = django.dispatch.Signal()

alert_group_escalation_snapshot_built = django.dispatch.Signal()

# Signal to rerender alert group in all connected integrations (Slack, Telegram) when its state is changed
alert_group_action_triggered_signal = django.dispatch.Signal()

# Signal to rerender alert group's log message in all connected integrations (Slack, Telegram)
# when alert group state is changed
alert_group_update_log_report_signal = django.dispatch.Signal()

# Signal to rerender alert group's resolution note in all connected integrations (Slack)
alert_group_update_resolution_note_signal = django.dispatch.Signal()

# Currently only writes error in Slack thread while notify user. Maybe it is worth to delete it?
user_notification_action_triggered_signal = django.dispatch.Signal()

alert_create_signal.connect(
    AlertGroupSlackRepresentative.on_create_alert,
)


alert_group_action_triggered_signal.connect(
    AlertGroupSlackRepresentative.on_alert_group_action_triggered,
)

alert_group_update_log_report_signal.connect(
    AlertGroupSlackRepresentative.on_alert_group_update_log_report,
)

alert_group_update_resolution_note_signal.connect(
    AlertGroupSlackRepresentative.on_alert_group_update_resolution_note,
)

user_notification_action_triggered_signal.connect(
    UserSlackRepresentative.on_user_action_triggered,
)
