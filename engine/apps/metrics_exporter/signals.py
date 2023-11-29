from apps.alerts.signals import alert_group_created_signal

from .tasks import update_metrics_for_new_alert_group


def on_alert_group_created(**kwargs):
    update_metrics_for_new_alert_group.apply_async((kwargs["alert_group"].id,))


alert_group_created_signal.connect(on_alert_group_created)
