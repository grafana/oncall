import logging
from typing import Optional

from django.urls import reverse

from apps.alerts.signals import user_notification_action_triggered_signal
from apps.exotel.models.phone_call import ExotelCallStatuses, ExotelPhoneCall
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


def get_call_status_callback_url():
    return create_engine_url(reverse("exotel:call_status_events"))


def update_exotel_call_status(call_id: str, call_status: str, user_choice: Optional[str] = None):
    from apps.base.models import UserNotificationPolicyLogRecord

    status_code = ExotelCallStatuses.DETERMINANT.get(call_status)
    if status_code is None:
        logger.warning(f"exotel.update_exotel_call_status: unexpected status call_id={call_id} status={call_status}")
        return

    exotel_phone_call = ExotelPhoneCall.objects.filter(call_id=call_id).first()
    if exotel_phone_call is None:
        logger.warning(f"exotel.update_exotel_call_status: exotel_phone_call not found call_id={call_id}")
        return

    logger.info(f"exotel.update_exotel_call_status: found exotel_phone_call call_id={call_id}")

    exotel_phone_call.status = status_code
    exotel_phone_call.save(update_fields=["status"])
    phone_call_record = exotel_phone_call.phone_call_record

    if phone_call_record is None:
        logger.warning(
            f"exotel.update_exotel_call_status: exotel_phone_call has no phone_call record call_id={call_id} "
            f"status={call_status}"
        )
        return

    logger.info(
        f"exotel.update_exotel_call_status: found phone_call_record id={phone_call_record.id} "
        f"call_id={call_id} status={call_status}"
    )
    log_record_type = None
    log_record_error_code = None

    success_statuses = [ExotelCallStatuses.COMPLETED]

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
            f"exotel.update_exotel_call_status: created log_record log_record_id={log_record.id} "
            f"type={log_record_type}"
        )

        user_notification_action_triggered_signal.send(sender=update_exotel_call_status, log_record=log_record)
