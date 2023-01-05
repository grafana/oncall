from celery.utils.log import get_task_logger
from django.conf import settings
from fcm_django.models import FCMDevice
from firebase_admin.messaging import APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message

from apps.alerts.models import AlertGroup
from apps.mobile_app.alert_rendering import get_push_notification_message
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


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

    device_to_notify = FCMDevice.objects.filter(user=user).first()

    # create an error log in case user has no devices set up
    if not device_to_notify:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Mobile push notification error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        logger.info(f"Error while sending a mobile push notification: user {user_pk} has no device set up")
        return

    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"
    number_of_alerts = alert_group.alerts.count()

    alert_title = "New Critical Alert" if critical else "New Alert"
    alert_subtitle = get_push_notification_message(alert_group)
    alert_body = f"Status: Firing"  # TODO: is there a better spot to calculate this rather than hardcoding?

    # TODO: we should update this to check if FCM_RELAY is set and conditionally make a call here..

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
            "body": f"{alert_subtitle}\n{alert_body}",
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

    logger.info(f"Sending push notification with message: {message}; thread-id: {thread_id};")

    fcm_response = device_to_notify.send_message(message)

    # NOTE: we may want to further handle the response from FCM, but for now lets simply log it out
    # https://firebase.google.com/docs/cloud-messaging/http-server-ref#interpret-downstream
    logger.info(f"FCM response was: {fcm_response}")
