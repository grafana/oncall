import logging
import typing

from .tasks import alert_group_created, alert_group_status_change

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OnAlertGroupCreatedKwargs(typing.TypedDict, total=False):
    alert_group: "AlertGroup"


class OnActionTriggeredKwargs(typing.TypedDict, total=False):
    log_record: "AlertGroupLogRecord"


def on_alert_group_created(**kwargs: typing.Unpack[OnAlertGroupCreatedKwargs]) -> None:
    alert_group = kwargs["alert_group"]

    # if we have an external_id, this alert_group was just created from a backsync update
    external_id = alert_group.external_ids.filter(source_alert_receive_channel=alert_group.channel).first()
    is_backsync = external_id is not None

    alert_group_created.apply_async((kwargs["alert_group"].id,), kwargs={"is_backsync": is_backsync})


def on_action_triggered(**kwargs: typing.Unpack[OnActionTriggeredKwargs]) -> None:
    from apps.alerts.constants import ActionSource
    from apps.alerts.models import AlertGroupLogRecord

    log_record = kwargs["log_record"]
    if not isinstance(log_record, AlertGroupLogRecord):
        try:
            log_record = AlertGroupLogRecord.objects.get(pk=log_record)
        except AlertGroupLogRecord.DoesNotExist:
            logger.warning(f"Webhook action triggered: log record {log_record} never created or has been deleted")
            return

    # keep track if this status change was triggered by a backsync event
    is_backsync = log_record.action_source == ActionSource.BACKSYNC
    alert_group_status_change.apply_async(
        (log_record.type, log_record.alert_group_id, log_record.author_id), kwargs={"is_backsync": is_backsync}
    )
