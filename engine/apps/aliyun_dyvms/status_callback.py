import logging
from typing import Optional

from apps.alerts.constants import ActionSource
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.utils import live_settings
from apps.aliyun_dyvms.models.phone_call import AliyunDyvmsCallStatuses, AliyunDyvmsPhoneCall

logger = logging.getLogger(__name__)


def update_aliyun_dyvms_call_status(call_id: str, status_code: str):
    from apps.base.models import UserNotificationPolicyLogRecord

    aliyun_phone_call = AliyunDyvmsPhoneCall.objects.filter(call_id=call_id).first()
    if aliyun_phone_call is None:
        logger.warning(
            f"aliyun_dyvms.update_aliyun_dyvms_call_status: aliyun_dyvms_phone_call not found call_id={call_id}")
        return

    logger.info(f"aliyun_dyvms.update_aliyun_dyvms_call_status: found aliyun_dyvms_phone_call call_id={call_id}")

    aliyun_phone_call.status = status_code
    aliyun_phone_call.save(update_fields=["status"])
    phone_call_record = aliyun_phone_call.phone_call_record

    if phone_call_record is None:
        logger.warning(
            f"aliyun_dyvms.update_aliyun_dyvms_call_status: aliyun_dyvms_phone_call has no phone_call record call_id={call_id} "
            f"status={status_code}"
        )
        return

    logger.info(
        f"aliyun_dyvms.update_aliyun_dyvms_call_status: found phone_call_record id={phone_call_record.id} "
        f"call_id={call_id} status={status_code}"
    )
    log_record_type = None
    log_record_error_code = None

    success_statuses = [AliyunDyvmsCallStatuses.USER_COMPLETED, AliyunDyvmsCallStatuses.USER_ABORTED]
    busy_statuses = [AliyunDyvmsCallStatuses.USER_BUSY]
    limited_statuses = [AliyunDyvmsCallStatuses.USER_CALL_LIMITED]
    no_answer_statuses = [AliyunDyvmsCallStatuses.USER_NO_ANSWER, AliyunDyvmsCallStatuses.USER_DENIED]

    if status_code in success_statuses:
        log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
    else:
        log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
        if status_code in busy_statuses:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_LINE_BUSY
        elif status_code in limited_statuses:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
        elif status_code in no_answer_statuses:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_NO_ANSWER
        else:
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
            f"aliyun_dyvms.update_aliyun_dyvms_call_status: created log_record log_record_id={log_record.id} "
            f"type={log_record_type}"
        )

        user_notification_action_triggered_signal.send(sender=update_aliyun_dyvms_call_status, log_record=log_record)
