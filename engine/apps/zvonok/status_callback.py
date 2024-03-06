import logging
from typing import Optional

from apps.alerts.constants import ActionSource
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.utils import live_settings
from apps.zvonok.models.phone_call import ZvonokCallStatuses, ZvonokPhoneCall

logger = logging.getLogger(__name__)


def update_zvonok_call_status(call_id: str, call_status: str, user_choice: Optional[str] = None):
    from apps.base.models import UserNotificationPolicyLogRecord

    status_code = ZvonokCallStatuses.DETERMINANT.get(call_status)
    if status_code is None:
        logger.warning(f"zvonok.update_zvonok_call_status: unexpected status call_id={call_id} status={call_status}")
        return

    zvonok_phone_call = ZvonokPhoneCall.objects.filter(call_id=call_id).first()
    if zvonok_phone_call is None:
        logger.warning(f"zvonok.update_zvonok_call_status: zvonok_phone_call not found call_id={call_id}")
        return

    logger.info(f"zvonok.update_zvonok_call_status: found zvonok_phone_call call_id={call_id}")

    zvonok_phone_call.status = status_code
    zvonok_phone_call.save(update_fields=["status"])
    phone_call_record = zvonok_phone_call.phone_call_record

    if phone_call_record is None:
        logger.warning(
            f"zvonok.update_zvonok_call_status: zvonok_phone_call has no phone_call record call_id={call_id} "
            f"status={call_status}"
        )
        return

    logger.info(
        f"zvonok.update_zvonok_call_status: found phone_call_record id={phone_call_record.id} "
        f"call_id={call_id} status={call_status}"
    )
    log_record_type = None
    log_record_error_code = None

    success_statuses = [ZvonokCallStatuses.USER, ZvonokCallStatuses.COMPL_FINISHED]

    if status_code in success_statuses:
        log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
    else:
        log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
        log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_FAILED

    if log_record_type is not None:
        log_record = UserNotificationPolicyLogRecord(
            type=log_record_type,
            notification_error_code=log_record_error_code,
            author=phone_call_record.receiver,
            notification_policy=phone_call_record.notification_policy,
            alert_group=phone_call_record.represents_alert_group,
            notification_step=phone_call_record.notification_policy.step
            if phone_call_record.notification_policy
            else None,
            notification_channel=phone_call_record.notification_policy.notify_by
            if phone_call_record.notification_policy
            else None,
        )
        log_record.save()
        logger.info(
            f"zvonok.update_zvonok_call_status: created log_record log_record_id={log_record.id} "
            f"type={log_record_type}"
        )

        user_notification_action_triggered_signal.send(sender=update_zvonok_call_status, log_record=log_record)

        if user_choice and user_choice == live_settings.ZVONOK_POSTBACK_USER_CHOICE_ACK:
            alert_group = phone_call_record.represents_alert_group
            user = phone_call_record.receiver
            logger.info(
                f"zvonok.update_zvonok_call_status: processing user choice"
                f" phone_call_record id={phone_call_record.id} zvonok_phone_call_id={call_id} "
                f"alert_group_id={alert_group.id} user_id={user.id}"
            )

            alert_group.acknowledge_by_user(user, action_source=ActionSource.PHONE)
