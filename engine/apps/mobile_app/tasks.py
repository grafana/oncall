import json
import logging

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from fcm_django.models import FCMDevice
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message
from requests import HTTPError
from rest_framework import status

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.mobile_app.alert_rendering import get_push_notification_message
from apps.user_management.models import User
from common.api_helpers.utils import create_engine_url
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk, critical):
    # avoid circular import
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} does not exist")
        return

    try:
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"User notification policy {notification_policy_pk} does not exist")
        return

    def _create_error_log_record():
        """
        Utility method to create a UserNotificationPolicyLogRecord with error
        """
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Mobile push notification error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )

    device_to_notify = FCMDevice.objects.filter(user=user).first()

    # create an error log in case user has no devices set up
    if not device_to_notify:
        _create_error_log_record()
        logger.error(f"Error while sending a mobile push notification: user {user_pk} has no device set up")
        return

    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"
    number_of_alerts = alert_group.alerts.count()

    alert_title = "New Critical Alert" if critical else "New Alert"
    alert_subtitle = get_push_notification_message(alert_group)

    status_verbose = "Firing"  # TODO: we should probably de-duplicate this text
    if alert_group.resolved:
        status_verbose = alert_group.get_resolve_text()
    elif alert_group.acknowledged:
        status_verbose = alert_group.get_acknowledge_text()

    if number_of_alerts <= 10:
        alerts_count_str = str(number_of_alerts)
    else:
        alert_count_rounded = (number_of_alerts // 10) * 10
        alerts_count_str = f"{alert_count_rounded}+"

    alert_body = f"Status: {status_verbose}, alerts: {alerts_count_str}"

    message = Message(
        token=device_to_notify.registration_id,
        data={
            # from the docs..
            # A dictionary of data fields (optional). All keys and values in the dictionary must be strings
            #
            # alert_group.status is an int so it must be casted...
            "orgId": alert_group.channel.organization.public_primary_key,
            "orgName": alert_group.channel.organization.stack_slug,
            "alertGroupId": alert_group.public_primary_key,
            "status": str(alert_group.status),
            "type": "oncall.critical_message" if critical else "oncall.message",
            "title": alert_title,
            "subtitle": alert_subtitle,
            "body": alert_body,
            "thread_id": thread_id,
        },
        apns=APNSConfig(
            payload=APNSPayload(
                aps=Aps(
                    thread_id=thread_id,
                    badge=number_of_alerts,
                    alert=ApsAlert(title=alert_title, subtitle=alert_subtitle, body=alert_body),
                    sound=CriticalSound(
                        critical=1 if critical else 0,
                        name="ambulance.aiff" if critical else "bingbong.aiff",
                        volume=1,
                    ),
                    custom_data={
                        "interruption-level": "critical" if critical else "time-sensitive",
                    },
                ),
            ),
        ),
    )

    logger.debug(f"Sending push notification with message: {message}; thread-id: {thread_id};")

    if settings.LICENSE == settings.OPEN_SOURCE_LICENSE_NAME:
        # FCM relay uses cloud connection to send push notifications
        from apps.oss_installation.models import CloudConnector

        if not CloudConnector.objects.exists():
            _create_error_log_record()
            logger.error(f"Error while sending a mobile push notification: not connected to cloud")
            return

        try:
            response = send_push_notification_to_fcm_relay(message)
            logger.debug(f"FCM relay response: {response}")
        except HTTPError as e:
            if status.HTTP_400_BAD_REQUEST <= e.response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
                # do not retry on HTTP client errors (4xx errors)
                _create_error_log_record()
                logger.error(
                    f"Error while sending a mobile push notification: HTTP client error {e.response.status_code}"
                )
                return
            else:
                raise
    else:
        # https://firebase.google.com/docs/cloud-messaging/http-server-ref#interpret-downstream
        response = device_to_notify.send_message(message)
        logger.debug(f"FCM response: {response}")

        if isinstance(response, FirebaseError):
            raise response


def send_push_notification_to_fcm_relay(message):
    """
    Send push notification to FCM relay on cloud instance: apps.mobile_app.fcm_relay.FCMRelayView
    """
    url = create_engine_url("mobile_app/v1/fcm_relay", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)

    response = requests.post(
        url, headers={"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}, json=json.loads(str(message))
    )
    response.raise_for_status()

    return response
