import logging

from .tasks import alert_group_created, alert_group_status_change

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def on_alert_group_created(**kwargs):
    alert_group_created.apply_async((kwargs["alert_group"].id,))


def on_action_triggered(**kwargs):
    from apps.alerts.models import AlertGroupLogRecord

    log_record = kwargs["log_record"]
    if not isinstance(log_record, AlertGroupLogRecord):
        log_record = AlertGroupLogRecord.objects.get(pk=log_record)
    alert_group_status_change.apply_async((log_record.type, log_record.alert_group_id, log_record.author_id))
