from django.apps import apps
from django.urls import reverse

from apps.alerts.signals import user_notification_action_triggered_signal
from apps.twilioapp.models import TwilioCallStatuses, TwilioPhoneCall, TwilioSMS, TwilioSMSstatuses
from common.api_helpers.utils import create_engine_url


def update_twilio_call_status(call_sid, call_status):
    """The function checks existence of TwilioPhoneCall instance
    according to call_sid and updates status on message_status

    Args:
        call_sid (str): sid of Twilio call
        call_status (str): new status

    Returns:

    """
    UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

    if call_sid and call_status:
        status = TwilioCallStatuses.DETERMINANT.get(call_status)

        twilio_phone_call = TwilioPhoneCall.objects.filter(sid=call_sid).first()

        # Check twilio phone call and then oncall phone call for backward compatibility after PhoneCall migration.
        # Will be removed soon.
        if twilio_phone_call:
            status = TwilioCallStatuses.DETERMINANT.get(call_status)
            twilio_phone_call.status = status
            twilio_phone_call.save(update_fields=["status"])
            oncall_phone_call = twilio_phone_call.oncall_phone_call
        else:
            OnCallPhoneCall = apps.get_model("phone_notifications", "OnCallPhoneCall")
            oncall_phone_call = OnCallPhoneCall.objects.filter(sid=call_sid).first()

        if oncall_phone_call and status:
            log_record_type = None
            log_record_error_code = None

            if status == TwilioCallStatuses.COMPLETED:
                log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
            elif status in [TwilioCallStatuses.FAILED, TwilioCallStatuses.BUSY, TwilioCallStatuses.NO_ANSWER]:
                log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
                log_record_error_code = get_error_code_by_twilio_status(status)

            if log_record_type is not None:
                log_record = UserNotificationPolicyLogRecord(
                    type=log_record_type,
                    notification_error_code=log_record_error_code,
                    author=oncall_phone_call.receiver,
                    notification_policy=oncall_phone_call.notification_policy,
                    alert_group=oncall_phone_call.represents_alert_group,
                    notification_step=oncall_phone_call.notification_policy.step
                    if oncall_phone_call.notification_policy
                    else None,
                    notification_channel=oncall_phone_call.notification_policy.notify_by
                    if oncall_phone_call.notification_policy
                    else None,
                )
                user_notification_action_triggered_signal.send(sender=update_twilio_call_status, log_record=log_record)


def get_error_code_by_twilio_status(status):
    UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
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
    UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

    if message_sid and message_status:
        status = TwilioSMSstatuses.DETERMINANT.get(message_status)

        twilio_sms = TwilioSMS.objects.filter(sid=message_sid).first()

        # Check twilio phone call and then oncall phone call for backward compatibility after PhoneCall migration.
        # Will be removed soon.
        if twilio_sms:
            twilio_sms.status = status
            twilio_sms.save(update_fields=["status"])
            oncall_sms = twilio_sms.oncall_sms
        else:
            OnCallPhoneCall = apps.get_model("phone_notifications", "OnCallPhoneCall")
            oncall_sms = OnCallPhoneCall.objects.filter(sid=message_sid).first()

        if oncall_sms and status:
            log_record_type = None
            log_record_error_code = None
            if status == TwilioSMSstatuses.DELIVERED:
                log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
            elif status in [TwilioSMSstatuses.UNDELIVERED, TwilioSMSstatuses.FAILED]:
                log_record_type = UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
                log_record_error_code = get_sms_error_code_by_twilio_status(status)

            if log_record_type is not None:
                log_record = UserNotificationPolicyLogRecord(
                    type=log_record_type,
                    notification_error_code=log_record_error_code,
                    author=oncall_sms.receiver,
                    notification_policy=oncall_sms.notification_policy,
                    alert_group=oncall_sms.represents_alert_group,
                    notification_step=oncall_sms.notification_policy.step if oncall_sms.notification_policy else None,
                    notification_channel=oncall_sms.notification_policy.notify_by
                    if oncall_sms.notification_policy
                    else None,
                )
                user_notification_action_triggered_signal.send(sender=update_twilio_sms_status, log_record=log_record)


def get_sms_error_code_by_twilio_status(status):
    UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
    TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
        TwilioSMSstatuses.UNDELIVERED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
        TwilioSMSstatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
    }
    return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)


def get_call_status_callback_url():
    return create_engine_url(reverse("twilioapp:call_status_events"), "https://pretty-mosh-97.loca.lt")


def get_sms_status_callback_url():
    return create_engine_url(reverse("twilioapp:sms_status_events"), "https://pretty-mosh-97.loca.lt")
