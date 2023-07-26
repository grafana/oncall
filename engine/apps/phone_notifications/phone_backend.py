import logging
from typing import Optional

import requests
from django.conf import settings

from apps.alerts.incident_appearance.renderers.phone_call_renderer import AlertGroupPhoneCallRenderer
from apps.alerts.incident_appearance.renderers.sms_renderer import AlertGroupSmsRenderer
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.utils import live_settings
from common.api_helpers.utils import create_engine_url
from common.utils import clean_markup

from .exceptions import (
    CallsLimitExceeded,
    FailedToMakeCall,
    FailedToSendSMS,
    NumberAlreadyVerified,
    NumberNotVerified,
    ProviderNotSupports,
    SMSLimitExceeded,
)
from .models import PhoneCallRecord, ProviderPhoneCall, ProviderSMS, SMSRecord
from .phone_provider import PhoneProvider, get_phone_provider

logger = logging.getLogger(__name__)


class PhoneBackend:
    def __init__(self):
        self.phone_provider: PhoneProvider = self._get_phone_provider()

    def _get_phone_provider(self) -> PhoneProvider:
        # wrapper to simplify mocking
        return get_phone_provider()

    def notify_by_call(self, user, alert_group, notification_policy):
        """
        notify_by_call makes a notification call to a user using configured phone provider or cloud notifications.
        It handles all business logic related to the call.
        """
        from apps.base.models import UserNotificationPolicyLogRecord

        log_record_error_code = None

        renderer = AlertGroupPhoneCallRenderer(alert_group)
        message = renderer.render()

        record = PhoneCallRecord(
            represents_alert_group=alert_group,
            receiver=user,
            notification_policy=notification_policy,
            exceeded_limit=False,
        )

        try:
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED and settings.IS_OPEN_SOURCE:
                self._notify_by_cloud_call(user, message)
                record.save()
            else:
                provider_call = self._notify_by_provider_call(user, message)
                # it is important that record is saved here, so it is possible to execute link_and_save
                record.save()
                if provider_call:
                    provider_call.link_and_save(record)
        except FailedToMakeCall:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL
        except ProviderNotSupports:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL
        except CallsLimitExceeded:
            record.exceeded_limit = True
            record.save()
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
        except NumberNotVerified:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED

        if log_record_error_code is not None:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=log_record_error_code,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
            log_record.save()
            user_notification_action_triggered_signal.send(sender=PhoneBackend.notify_by_call, log_record=log_record)

    def _notify_by_provider_call(self, user, message) -> Optional[ProviderPhoneCall]:
        """
        _notify_by_provider_call makes a notification call using configured phone provider.
        """
        if not self._validate_user_number(user):
            raise NumberNotVerified

        calls_left = self._validate_phone_calls_left(user)
        if calls_left <= 0:
            raise CallsLimitExceeded
        elif calls_left < 3:
            message = self._add_call_limit_warning(calls_left, message)
        return self.phone_provider.make_notification_call(user.verified_phone_number, message)

    def _notify_by_cloud_call(self, user, message):
        """
        _notify_by_cloud_call makes a call using connected Grafana Cloud Instance.
        This method should be  used only in OSS instances.
        """
        url = create_engine_url("api/v1/make_call", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)
        auth = {"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}
        data = {
            "email": user.email,
            "message": message,
        }
        try:
            response = requests.post(url, headers=auth, data=data, timeout=5)
        except requests.exceptions.RequestException as e:
            logger.error(f"PhoneBackend._notify_by_cloud_call: request exception {str(e)}")
            raise FailedToMakeCall
        if response.status_code == 200:
            logger.info("PhoneBackend._notify_by_cloud_call: OK")
        elif response.status_code == 400 and response.json().get("error") == "limit-exceeded":
            logger.info("PhoneBackend._notify_by_cloud_call: phone calls limit exceeded")
            raise CallsLimitExceeded
        elif response.status_code == 400 and response.json().get("error") == "number-not-verified":
            logger.info("PhoneBackend._notify_by_cloud_call: cloud number not verified")
            raise NumberNotVerified
        elif response.status_code == 404:
            logger.info(f"PhoneBackend._notify_by_cloud_call: user not found id={user.id} email={user.email}")
            raise FailedToMakeCall
        else:
            logger.error(f"PhoneBackend._notify_by_cloud_call: unexpected response code {response.status_code}")
            raise FailedToMakeCall

    def _add_call_limit_warning(self, calls_left, message):
        return f"{message} {calls_left} phone calls left. Contact your admin."

    def _validate_phone_calls_left(self, user) -> int:
        return user.organization.phone_calls_left(user)

    def notify_by_sms(self, user, alert_group, notification_policy):
        """
        notify_by_sms sends a notification sms to a user using configured phone provider.
        It handles business logic - limits, cloud notifications and UserNotificationPolicyLogRecord creation
        SMS itself is handled by phone provider.
        """

        from apps.base.models import UserNotificationPolicyLogRecord

        log_record_error_code = None

        renderer = AlertGroupSmsRenderer(alert_group)
        message = renderer.render()

        record = SMSRecord(
            represents_alert_group=alert_group,
            receiver=user,
            notification_policy=notification_policy,
            exceeded_limit=False,
        )

        try:
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED and settings.IS_OPEN_SOURCE:
                self._notify_by_cloud_sms(user, message)
                record.save()
            else:
                provider_sms = self._notify_by_provider_sms(user, message)
                record.save()
                if provider_sms:
                    provider_sms.link_and_save(record)
        except FailedToSendSMS:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS
        except ProviderNotSupports:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS
        except SMSLimitExceeded:
            record.exceeded_limit = True
            record.save()
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED
        except NumberNotVerified:
            log_record_error_code = UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED

        if log_record_error_code is not None:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=log_record_error_code,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
            log_record.save()
            user_notification_action_triggered_signal.send(sender=PhoneBackend.notify_by_sms, log_record=log_record)

    def _notify_by_provider_sms(self, user, message) -> Optional[ProviderSMS]:
        """
        _notify_by_provider_sms sends a notification sms using configured phone provider.
        """
        if not self._validate_user_number(user):
            raise NumberNotVerified

        sms_left = self._validate_sms_left(user)
        if sms_left <= 0:
            raise SMSLimitExceeded
        elif sms_left < 3:
            message = self._add_sms_limit_warning(sms_left, message)
        return self.phone_provider.send_notification_sms(user.verified_phone_number, message)

    def _notify_by_cloud_sms(self, user, message):
        """
        _notify_by_cloud_sms sends a sms using connected Grafana Cloud Instance.
        This method is used only in OSS instances.
        """
        url = create_engine_url("api/v1/send_sms", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)
        auth = {"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}
        data = {
            "email": user.email,
            "message": message,
        }
        try:
            response = requests.post(url, headers=auth, data=data, timeout=5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Unable to send SMS through cloud. Request exception {str(e)}")
            raise FailedToSendSMS
        if response.status_code == 200:
            logger.info("Sent cloud sms successfully")
        elif response.status_code == 400 and response.json().get("error") == "limit-exceeded":
            raise SMSLimitExceeded
        elif response.status_code == 400 and response.json().get("error") == "number-not-verified":
            raise NumberNotVerified
        elif response.status_code == 404:
            # user not found
            raise FailedToSendSMS
        else:
            raise FailedToSendSMS

    def _validate_sms_left(self, user) -> int:
        return user.organization.sms_left(user)

    def _add_sms_limit_warning(self, calls_left, message):
        return f"{message} {calls_left} sms left. Contact your admin."

    def _validate_user_number(self, user):
        return user.verified_phone_number is not None

    # relay calls/sms from oss related code
    def relay_oss_call(self, user, message):
        """
        relay_oss_call make phone call received from oss instance.
        Caller should handle exceptions raised by phone_provider.make_call.

        The difference between relay_oss_call and notify_by_call is that relay_oss_call uses phone_provider.make_call
        to only make call, not track status, gather digits or create logs.
        """
        if not self._validate_user_number(user):
            raise NumberNotVerified

        calls_left = self._validate_phone_calls_left(user)
        if calls_left <= 0:
            PhoneCallRecord.objects.create(
                receiver=user,
                exceeded_limit=True,
                grafana_cloud_notification=True,
            )
            raise CallsLimitExceeded
        elif calls_left < 3:
            message = self._add_call_limit_warning(calls_left, message)

        # additional cleaning, since message come from api call and wasn't cleaned by our renderer
        message = clean_markup(message).replace('"', "")

        self.phone_provider.make_call(user.verified_phone_number, message)
        # create PhoneCallRecord to track limits for calls from oss instances
        PhoneCallRecord.objects.create(
            receiver=user,
            exceeded_limit=False,
            grafana_cloud_notification=True,
        )

    def relay_oss_sms(self, user, message):
        """
        relay_oss_sms send sms  received from oss instance.
        Caller should handle exceptions raised by phone_provider.send_sms.

        The difference between relay_oss_sms and notify_by_sms is that relay_oss_call uses phone_provider.make_call
        to only send, not track status or create logs.
        """
        if not self._validate_user_number(user):
            raise NumberNotVerified

        sms_left = self._validate_sms_left(user)
        if sms_left <= 0:
            SMSRecord.objects.create(
                receiver=user,
                exceeded_limit=True,
                grafana_cloud_notification=True,
            )
            raise SMSLimitExceeded
        elif sms_left < 3:
            message = self._add_sms_limit_warning(sms_left, message)

        self.phone_provider.send_sms(user.verified_phone_number, message)
        SMSRecord.objects.create(
            receiver=user,
            exceeded_limit=False,
            grafana_cloud_notification=True,
        )

    # Number verification related code
    def send_verification_sms(self, user):
        """
        send_verification_sms sends a verification code to a user.
        Caller should handle exceptions raised by phone_provider.send_verification_sms.
        """
        logger.info(f"PhoneBackend.send_verification_sms: start verification for user {user.id}")
        if self._validate_user_number(user):
            logger.info(f"PhoneBackend.send_verification_sms: number already verified for user {user.id}")
            raise NumberAlreadyVerified
        self.phone_provider.send_verification_sms(user.unverified_phone_number)

    def make_verification_call(self, user):
        """
        make_verification_call makes a verification call  to a user.
        Caller should handle exceptions raised by phone_provider.make_verification_call
        """
        logger.info(f"PhoneBackend.make_verification_call: start verification user_id={user.id}")
        if self._validate_user_number(user):
            logger.info(f"PhoneBackend.make_verification_call: number already verified user_id={user.id}")
            raise NumberAlreadyVerified
        self.phone_provider.make_verification_call(user.unverified_phone_number)

    def verify_phone_number(self, user, code) -> bool:
        prev_number = user.verified_phone_number
        new_number = self.phone_provider.finish_verification(user.unverified_phone_number, code)
        if new_number:
            user.save_verified_phone_number(new_number)
            # TODO: move this to async task
            if prev_number:
                self._notify_disconnected_number(user, prev_number)
            self._notify_connected_number(user)
            logger.info(f"PhoneBackend.verify_phone_number: verified user_id={user.id}")
            return True
        else:
            logger.info(f"PhoneBackend.verify_phone_number: verification failed user_id={user.id}")
            return False

    def forget_number(self, user) -> bool:
        prev_number = user.verified_phone_number
        user.clear_phone_numbers()
        if prev_number:
            self._notify_disconnected_number(user, prev_number)
            return True
        return False

    def make_test_call(self, user):
        """
        make_test_call makes a test call to user's verified phone number
        Caller should handle exceptions raised by phone_provider.make_call.
        """
        text = "It is a test call from Grafana OnCall"
        if not user.verified_phone_number:
            raise NumberNotVerified
        self.phone_provider.make_call(user.verified_phone_number, text)

    def send_test_sms(self, user):
        """
        send_test_sms sends a test sms to user's verified phone number
        Caller should handle exceptions raised by phone_provider.send_sms.
        """
        text = "It is a test sms from Grafana OnCall"
        if not user.verified_phone_number:
            raise NumberNotVerified
        self.phone_provider.send_sms(user.verified_phone_number, text)

    def _notify_connected_number(self, user):
        text = (
            f"This phone number has been connected to Grafana OnCall team"
            f'"{user.organization.stack_slug}"\nYour Grafana OnCall <3'
        )
        try:
            if not user.verified_phone_number:
                logger.error("PhoneBackend._notify_connected_number: number not verified")
                return
            self.phone_provider.send_sms(user.verified_phone_number, text)
        except FailedToSendSMS:
            logger.error("PhoneBackend._notify_connected_number: failed")
        except ProviderNotSupports:
            logger.info("PhoneBackend._notify_connected_number: provider not supports sms")

    def _notify_disconnected_number(self, user, number):
        text = (
            f"This phone number has been disconnected from Grafana OnCall team"
            f'"{user.organization.stack_slug}"\nYour Grafana OnCall <3'
        )
        try:
            self.phone_provider.send_sms(number, text)
        except FailedToSendSMS:
            logger.error("PhoneBackend._notify_disconnected_number: failed")
        except ProviderNotSupports:
            logger.info("PhoneBackend._notify_disconnected_number: provider not supports sms")
