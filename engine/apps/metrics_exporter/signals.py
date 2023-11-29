from apps.alerts.constants import AlertGroupState
from apps.alerts.signals import alert_group_created_signal


def on_alert_group_created(**kwargs):
    alert_group = kwargs["alert_group"]
    if alert_group.is_maintenance_incident is True:
        return
    alert_group._update_metrics(
        organization_id=alert_group.channel.organization_id, previous_state=None, state=AlertGroupState.FIRING
    )


alert_group_created_signal.connect(on_alert_group_created)
