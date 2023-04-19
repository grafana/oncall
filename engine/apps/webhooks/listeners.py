import logging

from django.apps import apps

from .tasks import alert_group_created, alert_group_status_change

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def on_alert_group_created(**kwargs):
    alert_group_created.apply_async((kwargs["alert_group"],))


def on_action_triggered(**kwargs):
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
    log_record = kwargs["log_record"]
    if not isinstance(log_record, AlertGroupLogRecord):
        log_record = AlertGroupLogRecord.objects.get(pk=log_record)
    alert_group_status_change.apply_async((log_record.type, log_record.alert_group_id, log_record.author_id))
