import logging

from django.urls import reverse

from apps.alerts.signals import user_notification_action_triggered_signal
from apps.twilioapp.models import TwilioCallStatuses, TwilioPhoneCall, TwilioSMS, TwilioSMSstatuses
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


def update_twilio_call_status(call_sid, call_status):
    """The function checks existence of TwilioPhoneCall instance
    according to call_sid and updates status on message_status

    Args:
        call_sid (str): sid of Twilio call
        call_status (str): new status

    Returns:

    """
    from apps.base.models import UserNotificationPolicyLogRecord

    if call_sid and call_status:
        logger.info(f"twilioapp.update_twilio_call_status: processing sid={call_sid} status={call_status}")
        status_code = TwilioCallStatuses.DETERMINANT.get(call_status)

        if status_code is None:
            logger.warning(
                f"twilioapp.update_twilio_call_status: unexpected status sid={call_sid} status={call_status}"
            )
            return

        twilio_phone_call = TwilioPhoneCall.objects.filter(sid=call_sid).first()

        if twilio_phone_call is None:
            logger.warning(f"twilioapp.update_twilio_call_status: twilio_phone_call not found sid={call_sid}")
            return

        logger.info(f"twilioapp.update_twilio_call_status: found twilio_phone_call sid={call_sid}")
        twilio_phone_call.status = status_code
        twilio_phone_call.save(update_fields=["status"])
        phone_call_record = twilio_phone_call.phone_call_record

        if phone_call_record is None:
            logger.warning(
                f"twilioapp.update_twilio_call_status: twilio_phone_call has no phone_call record sid={call_sid} "
                f"status={call_status}"
            )
            return

        logger.info(
            f"twilioapp.update_twilio_call_status: found phone_call_record id={phone_call_record.id} "
            f"sid={call_sid} status={call_status}"
        )
        log_record_type = None
        log_record_error_code = None
        if status_code == TwilioCallStatuses.COMPLETED:
            log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
        elif status_code in [TwilioCallStatuses.FAILED, TwilioCallStatuses.BUSY, TwilioCallStatuses.NO_ANSWER]:
            log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
            log_record_error_code = get_error_code_by_twilio_status(status_code)
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
                f"twilioapp.update_twilio_call_status: created log_record log_record_id={log_record.id} "
                f"type={log_record_type}"
            )
            user_notification_action_triggered_signal.send(sender=update_twilio_call_status, log_record=log_record)


def get_error_code_by_twilio_status(status):
    from apps.base.models import UserNotificationPolicyLogRecord

    TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
        TwilioCallStatuses.BUSY: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_LINE_BUSY,
        TwilioCallStatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_FAILED,
        TwilioCallStatuses.NO_ANSWER: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_NO_ANSWER,
    }
    return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)


def update_twilio_sms_status(message_sid, message_status):
    """The function checks existence of SMSMessage
    instance according to message_sid and updates status on
    message_status

    Args:
        message_sid (str): sid of Twilio message
        message_status (str): new status

    Returns:

    """
    from apps.base.models import UserNotificationPolicyLogRecord

    if message_sid and message_status:
        logger.info(f"twilioapp.update_twilio_message_status: processing sid={message_sid} status={message_status}")
        status_code = TwilioSMSstatuses.DETERMINANT.get(message_status)
        if status_code is None:
            logger.warning(
                f"twilioapp.update_twilio_message_status: unexpected status sid={message_sid} status={message_status}"
            )
            return

        twilio_sms = TwilioSMS.objects.filter(sid=message_sid).first()
        if twilio_sms is None:
            logger.warning(f"twilioapp.update_twilio_message_status: twilio_sms not found sid={message_sid}")
            return

        logger.info(f"twilioapp.update_twilio_sms_status: found twilio_sms sid={message_sid}")
        twilio_sms.status = status_code
        twilio_sms.save(update_fields=["status"])
        sms_record = twilio_sms.sms_record

        if sms_record is None:
            logger.warning(f"twilioapp.update_twilio_sms_status: twilio_sms has no sms_record sid={message_sid}")
            return

        logger.info(
            f"twilioapp.update_twilio_sms_status: found sms_record id={sms_record.id} "
            f"sid={message_sid} status={message_status}"
        )
        log_record_type = None
        log_record_error_code = None
        if status_code == TwilioSMSstatuses.DELIVERED:
            log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
        elif status_code in [TwilioSMSstatuses.UNDELIVERED, TwilioSMSstatuses.FAILED]:
            log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
            log_record_error_code = get_sms_error_code_by_twilio_status(status_code)
        if log_record_type is not None:
            log_record = UserNotificationPolicyLogRecord(
                type=log_record_type,
                notification_error_code=log_record_error_code,
                author=sms_record.receiver,
                notification_policy=sms_record.notification_policy,
                alert_group=sms_record.represents_alert_group,
                notification_step=sms_record.notification_policy.step if sms_record.notification_policy else None,
                notification_channel=sms_record.notification_policy.notify_by
                if sms_record.notification_policy
                else None,
            )
            log_record.save()
            logger.info(
                f"twilioapp.update_twilio_sms_status: created log_record log_record_id={log_record.id} "
                f"type={log_record_type}"
            )
            user_notification_action_triggered_signal.send(sender=update_twilio_sms_status, log_record=log_record)


def get_sms_error_code_by_twilio_status(status):
    from apps.base.models import UserNotificationPolicyLogRecord

    TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
        TwilioSMSstatuses.UNDELIVERED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
        TwilioSMSstatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
    }
    return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)


def get_call_status_callback_url():
    return create_engine_url(reverse("twilioapp:call_status_events"))


def get_sms_status_callback_url():
    return create_engine_url(reverse("twilioapp:sms_status_events"))
