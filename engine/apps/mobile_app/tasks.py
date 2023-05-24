import json
import logging
import math
import typing
from enum import Enum

import humanize
import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import AndroidConfig, APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message
from requests import HTTPError
from rest_framework import status

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.mobile_app.alert_rendering import get_push_notification_message
from apps.schedules.models.on_call_schedule import OnCallSchedule, ScheduleEvent
from apps.user_management.models import User
from common.api_helpers.utils import create_engine_url
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import MobileAppUserSettings


MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


class MessageType(str, Enum):
    NORMAL = "oncall.message"
    CRITICAL = "oncall.critical_message"
    INFO = "oncall.info"


class FCMMessageData(typing.TypedDict):
    title: str
    subtitle: typing.Optional[str]
    body: typing.Optional[str]


def send_push_notification_to_fcm_relay(message: Message) -> requests.Response:
    """
    Send push notification to FCM relay on cloud instance: apps.mobile_app.fcm_relay.FCMRelayView
    """
    url = create_engine_url("mobile_app/v1/fcm_relay", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)

    response = requests.post(
        url, headers={"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}, json=json.loads(str(message))
    )
    response.raise_for_status()

    return response


def _send_push_notification(
    device_to_notify: FCMDevice, message: Message, error_cb: typing.Optional[typing.Callable[..., None]] = None
) -> None:
    logger.debug(f"Sending push notification with message: {message}")

    def _error_cb():
        if error_cb:
            error_cb()

    if settings.IS_OPEN_SOURCE:
        # FCM relay uses cloud connection to send push notifications
        from apps.oss_installation.models import CloudConnector

        if not CloudConnector.objects.exists():
            _error_cb()
            logger.error(f"Error while sending a mobile push notification: not connected to cloud")
            return

        try:
            response = send_push_notification_to_fcm_relay(message)
            logger.debug(f"FCM relay response: {response}")
        except HTTPError as e:
            if status.HTTP_400_BAD_REQUEST <= e.response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
                # do not retry on HTTP client errors (4xx errors)
                _error_cb()
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


def _construct_fcm_message(
    message_type: MessageType,
    device_to_notify: FCMDevice,
    thread_id: str,
    data: FCMMessageData,
    apns_payload: typing.Optional[APNSPayload] = None,
) -> Message:
    apns_config_kwargs = {}

    if apns_payload is not None:
        apns_config_kwargs["payload"] = apns_payload

    return Message(
        token=device_to_notify.registration_id,
        data={
            # from the docs..
            # A dictionary of data fields (optional). All keys and values in the dictionary must be strings
            **data,
            "type": message_type,
            "thread_id": thread_id,
        },
        android=AndroidConfig(
            # from the docs
            # https://firebase.google.com/docs/cloud-messaging/concept-options#setting-the-priority-of-a-message
            #
            # Normal priority.
            # Normal priority messages are delivered immediately when the app is in the foreground.
            # For backgrounded apps, delivery may be delayed. For less time-sensitive messages, such as notifications
            # of new email, keeping your UI in sync, or syncing app data in the background, choose normal delivery
            # priority.
            #
            # High priority.
            # FCM attempts to deliver high priority messages immediately even if the device is in Doze mode.
            # High priority messages are for time-sensitive, user visible content.
            priority="high",
        ),
        apns=APNSConfig(
            **apns_config_kwargs,
            headers={
                # From the docs
                # https://firebase.google.com/docs/cloud-messaging/concept-options#setting-the-priority-of-a-message
                "apns-priority": "10",
            },
        ),
    )


def _get_alert_group_escalation_fcm_message(
    alert_group: AlertGroup, user: User, device_to_notify: FCMDevice, critical: bool
) -> Message:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

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

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

    # critical defines the type of notification.
    # we use overrideDND to establish if the notification should sound even if DND is on
    overrideDND = critical and mobile_app_user_settings.important_notification_override_dnd

    # APNS only allows to specify volume for critical notifications
    apns_volume = mobile_app_user_settings.important_notification_volume if critical else None
    apns_sound_name = (
        mobile_app_user_settings.important_notification_sound_name
        if critical
        else mobile_app_user_settings.default_notification_sound_name
    ) + MobileAppUserSettings.IOS_SOUND_NAME_EXTENSION  # iOS app expects the filename to have an extension

    fcm_message_data: FCMMessageData = {
        "title": alert_title,
        "subtitle": alert_subtitle,
        "body": alert_body,
        "orgId": alert_group.channel.organization.public_primary_key,
        "orgName": alert_group.channel.organization.stack_slug,
        "alertGroupId": alert_group.public_primary_key,
        # alert_group.status is an int so it must be casted...
        "status": str(alert_group.status),
        # Pass user settings, so the Android app can use them to play the correct sound and volume
        "default_notification_sound_name": (
            mobile_app_user_settings.default_notification_sound_name
            + MobileAppUserSettings.ANDROID_SOUND_NAME_EXTENSION
        ),
        "default_notification_volume_type": mobile_app_user_settings.default_notification_volume_type,
        "default_notification_volume": str(mobile_app_user_settings.default_notification_volume),
        "default_notification_volume_override": json.dumps(
            mobile_app_user_settings.default_notification_volume_override
        ),
        "important_notification_sound_name": (
            mobile_app_user_settings.important_notification_sound_name
            + MobileAppUserSettings.ANDROID_SOUND_NAME_EXTENSION
        ),
        "important_notification_volume_type": mobile_app_user_settings.important_notification_volume_type,
        "important_notification_volume": str(mobile_app_user_settings.important_notification_volume),
        "important_notification_volume_override": json.dumps(
            mobile_app_user_settings.important_notification_volume_override
        ),
        "important_notification_override_dnd": json.dumps(mobile_app_user_settings.important_notification_override_dnd),
    }

    apns_payload = APNSPayload(
        aps=Aps(
            thread_id=thread_id,
            badge=number_of_alerts,
            alert=ApsAlert(title=alert_title, subtitle=alert_subtitle, body=alert_body),
            sound=CriticalSound(
                # The notification shouldn't be critical if the user has disabled "override DND" setting
                critical=overrideDND,
                name=apns_sound_name,
                volume=apns_volume,
            ),
            custom_data={
                "interruption-level": "critical" if overrideDND else "time-sensitive",
            },
        ),
    )

    message_type = MessageType.CRITICAL if critical else MessageType.NORMAL

    return _construct_fcm_message(message_type, device_to_notify, thread_id, fcm_message_data, apns_payload)


def _get_youre_going_oncall_fcm_message(
    user: User, schedule: OnCallSchedule, device_to_notify: FCMDevice, seconds_until_going_oncall: int
) -> Message:
    thread_id = f"{schedule.public_primary_key}:{user.public_primary_key}:going-oncall"

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

    notification_title = (
        f"You are going on call in {humanize.naturaldelta(seconds_until_going_oncall)} for schedule {schedule.name}"
    )

    data: FCMMessageData = {
        "title": notification_title,
        "info_notification_sound_name": (
            mobile_app_user_settings.info_notification_sound_name + MobileAppUserSettings.ANDROID_SOUND_NAME_EXTENSION
        ),
        "info_notification_volume_type": mobile_app_user_settings.info_notification_volume_type,
        "info_notification_volume": str(mobile_app_user_settings.info_notification_volume),
        "info_notification_volume_override": json.dumps(mobile_app_user_settings.info_notification_volume_override),
    }

    apns_payload = APNSPayload(
        aps=Aps(
            thread_id=thread_id,
            alert=ApsAlert(title=notification_title),
            sound=CriticalSound(
                critical=False,
                name=mobile_app_user_settings.info_notification_sound_name
                + MobileAppUserSettings.IOS_SOUND_NAME_EXTENSION,
            ),
            custom_data={
                "interruption-level": "time-sensitive",
            },
        ),
    )

    return _construct_fcm_message(MessageType.INFO, device_to_notify, thread_id, data, apns_payload)


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

    message = _get_alert_group_escalation_fcm_message(alert_group, user, device_to_notify, critical)
    _send_push_notification(device_to_notify, message, _create_error_log_record)


def _shift_starts_within_range(
    timing_window_lower: int, timing_window_upper: int, seconds_until_shift_starts: int
) -> bool:
    return timing_window_lower <= seconds_until_shift_starts <= timing_window_upper


def should_we_send_going_oncall_push_notification(
    now: timezone.datetime, user_settings: "MobileAppUserSettings", schedule_event: ScheduleEvent
) -> typing.Optional[int]:
    """
    If the user should be set a "you're going oncall" push notification, return the number of seconds
    until they will be going oncall.

    If no notification should be sent, return None.

    Currently we will send notifications for the following scenarios:
    - schedule is starting in user's "configured notification timing preference" +/- a 4 minute buffer
    - schedule is starting within the next fifteen minutes

    Returns `None` if conditions are not met for the user to receive a push notification. Otherwise returns
    an `int` which represents the # of seconds until the oncall shift starts.
    """
    NOTIFICATION_TIMING_BUFFER = 7 * 60  # 7 minutes in seconds
    FIFTEEN_MINUTES_IN_SECONDS = 15 * 60

    # this _should_ always be positive since final_events is returning only events in the future
    seconds_until_shift_starts = math.floor((schedule_event["start"] - now).total_seconds())

    user_wants_to_receive_info_notifications = user_settings.info_notifications_enabled
    # int representing num of seconds before the shift starts that the user wants to be notified
    user_notification_timing_preference = user_settings.going_oncall_notification_timing

    if not user_wants_to_receive_info_notifications:
        logger.info("not sending going oncall push notification because info_notifications_enabled is false")
        return

    # 14 minute window where the notification could be sent (7 mins before or 7 mins after)
    timing_window_lower = user_notification_timing_preference - NOTIFICATION_TIMING_BUFFER
    timing_window_upper = user_notification_timing_preference + NOTIFICATION_TIMING_BUFFER

    shift_starts_within_users_notification_timing_preference = _shift_starts_within_range(
        timing_window_lower, timing_window_upper, seconds_until_shift_starts
    )
    shift_starts_within_fifteen_minutes = _shift_starts_within_range(
        0, FIFTEEN_MINUTES_IN_SECONDS, seconds_until_shift_starts
    )

    timing_logging_msg = (
        f"seconds_until_shift_starts: {seconds_until_shift_starts}\n"
        f"user_notification_timing_preference: {user_notification_timing_preference}\n"
        f"timing_window_lower: {timing_window_lower}\n"
        f"timing_window_upper: {timing_window_upper}\n"
        f"shift_starts_within_users_notification_timing_preference: {shift_starts_within_users_notification_timing_preference}\n"
        f"shift_starts_within_fifteen_minutes: {shift_starts_within_fifteen_minutes}"
    )

    # Temporary remove `shift_starts_within_users_notification_timing_preference` from condition to send notification only 15 minutes before the shift starts
    # TODO: Return it once mobile app ready and default value is changed (https://github.com/grafana/oncall/issues/1999)
    if shift_starts_within_fifteen_minutes:
        logger.info(f"timing is right to send going oncall push notification\n{timing_logging_msg}")
        return seconds_until_shift_starts
    logger.info(f"timing is not right to send going oncall push notification\n{timing_logging_msg}")


def _generate_going_oncall_push_notification_cache_key(user_pk: str, schedule_event: ScheduleEvent) -> str:
    return f"going_oncall_push_notification:{user_pk}:{schedule_event['shift']['pk']}"


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def conditionally_send_going_oncall_push_notifications_for_schedule(schedule_pk) -> None:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

    PUSH_NOTIFICATION_TRACKING_CACHE_KEY_TTL = 60 * 60  # 60 minutes
    user_cache: typing.Dict[str, User] = {}
    device_cache: typing.Dict[str, FCMDevice] = {}

    logger.info(f"Start calculate_going_oncall_push_notifications_for_schedule for schedule {schedule_pk}")

    try:
        schedule: OnCallSchedule = OnCallSchedule.objects.get(pk=schedule_pk)
    except OnCallSchedule.DoesNotExist:
        logger.info(f"Tried to notify user about going on-call for non-existing schedule {schedule_pk}")
        return

    now = timezone.now()
    schedule_final_events = schedule.final_events("UTC", now, days=7)

    relevant_cache_keys = [
        _generate_going_oncall_push_notification_cache_key(user["pk"], schedule_event)
        for schedule_event in schedule_final_events
        for user in schedule_event["users"]
    ]

    relevant_notifications_already_sent = cache.get_many(relevant_cache_keys)

    for schedule_event in schedule_final_events:
        users = schedule_event["users"]

        for user in users:
            user_pk = user["pk"]
            logger.info(f"Evaluating if we should send push notification for schedule {schedule_pk} for user {user_pk}")

            user = user_cache.get(user_pk, None)
            if user is None:
                try:
                    user = User.objects.get(public_primary_key=user_pk)
                    user_cache[user_pk] = user
                except User.DoesNotExist:
                    logger.warning(f"User {user_pk} does not exist")
                    continue

            device_to_notify = device_cache.get(user_pk, None)
            if device_to_notify is None:
                device_to_notify = FCMDevice.objects.filter(user=user).first()

                if not device_to_notify:
                    logger.info(f"User {user_pk} has no device set up")
                    continue
                else:
                    device_cache[user_pk] = device_to_notify

            mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

            cache_key = _generate_going_oncall_push_notification_cache_key(user_pk, schedule_event)
            already_sent_this_push_notification = cache_key in relevant_notifications_already_sent
            seconds_until_going_oncall = should_we_send_going_oncall_push_notification(
                now, mobile_app_user_settings, schedule_event
            )

            if seconds_until_going_oncall is not None and not already_sent_this_push_notification:
                message = _get_youre_going_oncall_fcm_message(
                    user, schedule, device_to_notify, seconds_until_going_oncall
                )
                _send_push_notification(device_to_notify, message)
                cache.set(cache_key, True, PUSH_NOTIFICATION_TRACKING_CACHE_KEY_TTL)
            else:
                logger.info(
                    f"Skipping sending going oncall push notification for user {user_pk} and shift {schedule_event['shift']['pk']}. "
                    f"Already sent: {already_sent_this_push_notification}"
                )


@shared_dedicated_queue_retry_task()
def conditionally_send_going_oncall_push_notifications_for_all_schedules() -> None:
    for schedule in OnCallSchedule.objects.all():
        conditionally_send_going_oncall_push_notifications_for_schedule.apply_async((schedule.pk,))
