import logging

from django.dispatch import receiver

from apps.alerts.signals import alert_create_signal, alert_group_action_triggered_signal

logger = logging.getLogger(__name__)


@receiver(alert_create_signal)
def on_alert_created(sender, alert, **kwargs):
    """Handle alert creation - send notification to Zoom channel."""
    from apps.alerts.models import Alert
    from apps.zoom.tasks import on_create_alert_async

    # alert can be either an int (id) or an object
    if isinstance(alert, int):
        try:
            alert_obj = Alert.objects.get(pk=alert)
        except Alert.DoesNotExist:
            logger.warning(f"Alert {alert} not found")
            return
    else:
        alert_obj = alert

    alert_group = alert_obj.group
    if alert_group.channel.organization.zoom_channels.filter(is_default_channel=True).exists():
        logger.info(f"Triggering Zoom notification for alert {alert_obj.pk}")
        on_create_alert_async.delay(alert_pk=alert_obj.pk)


@receiver(alert_group_action_triggered_signal)
def on_alert_group_action_triggered(sender, log_record, **kwargs):
    """Handle alert group action - update Zoom message."""
    from apps.alerts.models import AlertGroupLogRecord
    from apps.zoom.tasks import on_alert_group_action_triggered_async

    # log_record can be either an int (id) or an object
    if isinstance(log_record, int):
        try:
            log_record_obj = AlertGroupLogRecord.objects.get(pk=log_record)
        except AlertGroupLogRecord.DoesNotExist:
            logger.warning(f"AlertGroupLogRecord {log_record} not found")
            return
    else:
        log_record_obj = log_record

    alert_group = log_record_obj.alert_group
    if alert_group.zoom_messages.exists():
        on_alert_group_action_triggered_async.delay(log_record_id=log_record_obj.pk)
