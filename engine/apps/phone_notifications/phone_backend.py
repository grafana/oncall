import logging

import requests
from django.apps import apps
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
from .models import OnCallPhoneCall, OnCallSMS
from .phone_provider import PhoneProvider, get_phone_provider

logger = logging.getLogger(__name__)


class PhoneBackend:
    def __init__(self):
        self.phone_provider: PhoneProvider = get_phone_provider()

    def notify_by_call(self, user, alert_group, notification_policy):
        """
        notify_by_call makes a notification call to a user using configured phone provider.
        It handles business logic - limits, cloud notifications and UserNotificationPolicyLogRecord creation.
        Call itself is handled by phone provider.
        """
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
        log_record = None

        renderer = AlertGroupPhoneCallRenderer(alert_group)
        message = renderer.render()

        call = OnCallPhoneCall.objects.create(
            represents_alert_group=alert_group,
            receiver=user,
            notification_policy=notification_policy,
            exceeded_limit=False,
        )

        try:
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                self.make_cloud_call(user, message)
            else:
                if not user.verified_phone_number:
                    raise NumberNotVerified
                calls_left = user.organization.phone_calls_left(user)
                if calls_left <= 0:
                    call.exceeded_limit = True
                    call.save()
                    raise CallsLimitExceeded("Organization calls limit exceeded")
                if calls_left < 3:
                    message += f"{calls_left} phone calls left. Contact your admin."
                self.phone_provider.make_notification_call(user.verified_phone_number, message, call)
        except FailedToMakeCall:
            call.delete()
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except CallsLimitExceeded:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except NumberNotVerified:
            call.delete()
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except ProviderNotSupports:
            call.delete()
            # TODO: phone_provider: choose error code for ProviderNotSupports
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )

        # Why there is no log record for TYPE_PERSONAL_NOTIFICATION_SUCCESS?
        # For twilio we are receiving callback in Status API View,
        # CloudPhoneNotifications doesn't support sending statuses on call
        # If any of the future phone providers will have the ability to provide delivered status in the response to making call
        # Feel free to place it appropriate log record here.

        if log_record is not None:
            log_record.save()
            user_notification_action_triggered_signal.send(sender=PhoneBackend.notify_by_call, log_record=log_record)

    def notify_by_sms(self, user, alert_group, notification_policy):
        """
        notify_by_sms sends a notification sms to a user using configured phone provider.
        It handles business logic - limits, cloud notifications and UserNotificationPolicyLogRecord creation
        SMS itself is handled by phone provider.
        """

        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
        log_record = None

        renderer = AlertGroupSmsRenderer(alert_group)
        message = renderer.render()

        sms = OnCallSMS.objects.create(
            represents_alert_group=alert_group,
            receiver=user,
            notification_policy=notification_policy,
            exceeded_limit=False,
        )

        try:
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                self.send_cloud_sms(user, message)
            else:
                if not user.verified_phone_number:
                    raise NumberNotVerified

                sms_left = user.organization.sms_left(user)
                if sms_left <= 0:
                    sms.exceeded_limit = True
                    sms.save()
                    raise SMSLimitExceeded
                if sms_left < 3:
                    message += " {} sms left. Contact your admin.".format(sms_left)

                self.phone_provider.send_notification_sms(user.verified_phone_number, message, sms)
        except FailedToSendSMS:
            sms.delete()
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except SMSLimitExceeded:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except NumberNotVerified:
            sms.delete()
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except ProviderNotSupports:
            sms.delete()
            # TODO: phone_provider: choose error code for ProviderNotSupports
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )

        if log_record is not None:
            log_record.save()
            user_notification_action_triggered_signal.send(sender=PhoneBackend.notify_by_sms, log_record=log_record)

    def relay_oss_call(self, user, message):
        """
        relay_oss_call execute phone call received from oss instances.
        """
        # some additional cleaning, since message come from outside and wasn't cleaned by our renderer
        message = clean_markup(message)
        self.phone_provider.make_call(message, user.verified_phone_number)

    def relay_oss_sms(self, user, message):
        """
        relay_oss_call execute phone call received from oss instances.
        """
        # some additional cleaning, since message come from outside and wasn't cleaned by our renderer
        self.phone_provider.send_sms(message, user.verified_phone_number)

    def make_cloud_call(self, user, message):
        """
        make_cloud_call makes a call using connected Grafana Cloud Instances.
        This method is used only in OSS instances.
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
            logger.error(f"CloudPhoneProvider.make_notification_call: request exception {str(e)}")
            raise FailedToMakeCall
        if response.status_code == 200:
            logger.info("CloudPhoneProvider.make_notification_call: OK")
        elif response.status_code == 400 and response.json().get("error") == "limit-exceeded":
            logger.error(f"CloudPhoneProvider.make_notification_call: cloud phone calls limit exceeded")
            raise CallsLimitExceeded
        elif response.status_code == 404:
            logger.error(f"CloudPhoneProvider.make_notification_call: user {user.email} not found")
            raise FailedToMakeCall
        else:
            logger.error(f"CloudPhoneProvider.make_notification_call: unexpected response code {response.status_code}")
            raise FailedToMakeCall

    def send_cloud_sms(self, user, message):
        """
        send_cloud_sms sends a sms using connected Grafana Cloud Instances.
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
        elif response.status_code == 404:
            # user not found
            raise FailedToSendSMS
        else:
            raise FailedToSendSMS

    # Number verification related code
    def send_verification_sms(self, user):
        """
        send_verification_sms sends a verification code to a user.
        """
        logger.info(f"PhoneBackend.send_verification_sms: start verification for user {user.id}")
        if user.verified_phone_number:
            logger.info(f"PhoneBackend.send_verification_sms: number already verified for user {user.id}")
            raise NumberAlreadyVerified
        self.phone_provider.send_verification_sms(user.unverified_phone_number)

    def make_verification_call(self, user):
        """
        make_verification_call makes a verification call  to a user.
        """
        logger.info(f"PhoneBackend.make_verification_call: start verification for user {user.id}")
        if user.verified_phone_number:
            logger.info(f"PhoneBackend.make_verification_call: number already verified for user {user.id}")
            raise NumberAlreadyVerified
        self.phone_provider.make_verification_call(user)

    def verify_phone_number(self, user, code) -> bool:
        logger.info(f"PhoneBackend.verify_phone_number: finish verification process for {user.id}")
        prev_number = user.verified_phone_number
        new_number = self.phone_provider.finish_verification(user.unverified_phone_number, code)
        if new_number:
            user.save_verified_phone_number(new_number)
            if prev_number:
                self._notify_disconnected_number(user, prev_number)
            self._notify_connected_number(user)
            return True
        else:
            return False

    def forget_number(self, user) -> bool:
        prev_number = user.verified_phone_number
        user.clear_phone_numbers()
        if prev_number:
            self._notify_disconnected_number(user, prev_number)
            return True
        return False

    def make_test_call(self, user):
        text = "It is a test call from Grafana OnCall"
        try:
            self.phone_provider.make_call(user, text)
        except (FailedToMakeCall, ProviderNotSupports):
            logger.error("tbd")

    def _notify_connected_number(self, user):
        text = (
            f"This phone number has been connected to Grafana OnCall team"
            f'"{user.organization.stack_slug}"\nYour Grafana OnCall <3'
        )
        try:
            self.phone_provider.send_sms(user.verified_phone_number, text)
        except (FailedToSendSMS, ProviderNotSupports):
            logger.error("tbd")

    def _notify_disconnected_number(self, user, number):
        text = (
            f"This phone number has been disconnected from Grafana OnCall team"
            f'"{user.organization.stack_slug}"\nYour Grafana OnCall <3'
        )
        try:
            self.phone_provider.send_sms(number, text)
        except (FailedToSendSMS, ProviderNotSupports):
            logger.error("tbd")
