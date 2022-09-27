import logging

from django.apps import apps

from apps.alerts.models import AlertGroup

from .tasks import on_create_alert_async, on_update_alert_async, on_update_log_record_async

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Listeners for alert create/update signals (see signals.py).
# Get/Validate any needed information and trigger async task (see tasks.py).


def on_alert_created(**kwargs):
    alert_pk = kwargs["alert"]
    on_create_alert_async.apply_async((alert_pk,))


def on_action_triggered(**kwargs):
    AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
    log_record = kwargs["log_record"]
    if not isinstance(log_record, AlertGroupLogRecord):
        log_record = AlertGroupLogRecord.objects.get(pk=log_record)
    on_update_alert_async.apply_async((log_record.alert_group.pk,))


def on_update_log_report(**kwargs):
    alert_group = kwargs["alert_group"]

    if not isinstance(alert_group, AlertGroup):
        alert_group = AlertGroup.all_objects.get(pk=alert_group)

    on_update_log_record_async.apply_async((alert_group.pk,))
