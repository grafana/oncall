import datetime
import json
import logging
import math
import typing
from enum import Enum

import humanize
import pytz
import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.db.models import DateTimeField, ExpressionWrapper, F, Max, QuerySet
from django.utils import timezone
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import AndroidConfig, APNSConfig, APNSPayload, Aps, ApsAlert, CriticalSound, Message
from requests import HTTPError
from rest_framework import status

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.mobile_app.alert_rendering import get_push_notification_subtitle
from apps.schedules.models import ShiftSwapRequest
from apps.schedules.models.on_call_schedule import OnCallSchedule, ScheduleEvent
from apps.user_management.models import User
from common.api_helpers.utils import create_engine_url
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.l10n import format_localized_datetime, format_localized_time

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings


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
    device_to_notify: "FCMDevice", message: Message, error_cb: typing.Optional[typing.Callable[..., None]] = None
) -> None:
    logger.debug(f"Sending push notification to device type {device_to_notify.type} with message: {message}")

    def _error_cb():
        if error_cb:
            error_cb()

    if settings.IS_OPEN_SOURCE:
        # FCM relay uses cloud connection to send push notifications
        from apps.oss_installation.models import CloudConnector

        if not CloudConnector.objects.exists():
            _error_cb()
            logger.error("Error while sending a mobile push notification: not connected to cloud")
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
    device_to_notify: "FCMDevice",
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
    alert_group: AlertGroup, user: User, device_to_notify: "FCMDevice", critical: bool
) -> Message:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"{alert_group.channel.organization.public_primary_key}:{alert_group.public_primary_key}"

    alert_title = "New Important Alert" if critical else "New Alert"
    alert_subtitle = get_push_notification_subtitle(alert_group)

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

    number_of_alerts = alert_group.alerts.count()
    apns_payload = APNSPayload(
        aps=Aps(
            thread_id=thread_id,
            badge=number_of_alerts,
            alert=ApsAlert(title=alert_title, subtitle=alert_subtitle),
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


def _get_youre_going_oncall_notification_title(seconds_until_going_oncall: int) -> str:
    return f"Your on-call shift starts in {humanize.naturaldelta(seconds_until_going_oncall)}"


def _get_shift_subtitle(
    schedule: OnCallSchedule,
    shift_start: datetime.datetime,
    shift_end: datetime.datetime,
    mobile_app_user_settings: "MobileAppUserSettings",
) -> str:
    shift_starts_and_ends_on_same_day = shift_start.date() == shift_end.date()
    dt_formatter_func = format_localized_time if shift_starts_and_ends_on_same_day else format_localized_datetime

    def _format_datetime(dt: datetime.datetime) -> str:
        """
        1. Convert the shift datetime to the user's mobile device's timezone
        2. Display the timezone aware datetime as a formatted string that is based on the user's configured mobile
        app locale, otherwise fallback to "en"
        """
        localized_dt = dt.astimezone(pytz.timezone(mobile_app_user_settings.time_zone))
        return dt_formatter_func(localized_dt, mobile_app_user_settings.locale)

    formatted_shift = f"{_format_datetime(shift_start)} - {_format_datetime(shift_end)}"

    return f"{formatted_shift}\nSchedule {schedule.name}"


def _get_youre_going_oncall_fcm_message(
    user: User,
    schedule: OnCallSchedule,
    device_to_notify: "FCMDevice",
    seconds_until_going_oncall: int,
    schedule_event: ScheduleEvent,
) -> Message:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"{schedule.public_primary_key}:{user.public_primary_key}:going-oncall"

    mobile_app_user_settings, _ = MobileAppUserSettings.objects.get_or_create(user=user)

    notification_title = _get_youre_going_oncall_notification_title(seconds_until_going_oncall)
    notification_subtitle = _get_shift_subtitle(
        schedule, schedule_event["start"], schedule_event["end"], mobile_app_user_settings
    )

    data: FCMMessageData = {
        "title": notification_title,
        "subtitle": notification_subtitle,
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
            alert=ApsAlert(title=notification_title, subtitle=notification_subtitle),
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
    from apps.mobile_app.models import FCMDevice

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
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

    device_to_notify = FCMDevice.get_active_device_for_user(user)

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
    now: datetime.datetime, user_settings: "MobileAppUserSettings", schedule_event: ScheduleEvent
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
        return None

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
    return None


def _generate_going_oncall_push_notification_cache_key(user_pk: str, schedule_event: ScheduleEvent) -> str:
    return f"going_oncall_push_notification:{user_pk}:{schedule_event['shift']['pk']}"


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def conditionally_send_going_oncall_push_notifications_for_schedule(schedule_pk) -> None:
    # avoid circular import
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings

    PUSH_NOTIFICATION_TRACKING_CACHE_KEY_TTL = 60 * 60  # 60 minutes
    user_cache: typing.Dict[str, User] = {}
    device_cache: typing.Dict[str, "FCMDevice"] = {}

    logger.info(f"Start calculate_going_oncall_push_notifications_for_schedule for schedule {schedule_pk}")

    try:
        schedule: OnCallSchedule = OnCallSchedule.objects.get(pk=schedule_pk)
    except OnCallSchedule.DoesNotExist:
        logger.info(f"Tried to notify user about going on-call for non-existing schedule {schedule_pk}")
        return

    now = timezone.now()
    datetime_end = now + datetime.timedelta(days=7)
    schedule_final_events = schedule.final_events(now, datetime_end)

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
                device_to_notify = FCMDevice.get_active_device_for_user(user)

                if not device_to_notify:
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
                    user, schedule, device_to_notify, seconds_until_going_oncall, schedule_event
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


EARLIEST_NOTIFICATION_OFFSET = datetime.timedelta(weeks=4)
WINDOW = datetime.timedelta(days=1)


@shared_dedicated_queue_retry_task()
def notify_shift_swap_requests() -> None:
    if not settings.FEATURE_SHIFT_SWAPS_ENABLED:
        return

    for shift_swap_request in _get_shift_swap_requests_to_notify(timezone.now()):
        notify_shift_swap_request.delay(shift_swap_request.pk)


def _get_shift_swap_requests_to_notify(now: datetime.datetime) -> QuerySet[ShiftSwapRequest]:
    # This is the same as notification_window_start = max(created_at, swap_start - EARLIEST_NOTIFICATION_OFFSET)
    notification_window_start = Max(
        F("created_at"), ExpressionWrapper(F("swap_start") - EARLIEST_NOTIFICATION_OFFSET, output_field=DateTimeField())
    )

    # This is the same as notification_window_end = notification_window_start + WINDOW
    notification_window_end = ExpressionWrapper(F("notification_window_start") + WINDOW, output_field=DateTimeField())

    # For every shift swap request, we assign a window of time in which we can notify users about it.
    # Here we select all the shift swap requests for which now is within its notification window.
    return ShiftSwapRequest.objects.annotate(
        notification_window_start=notification_window_start,
        notification_window_end=notification_window_end,
    ).filter(
        benefactor__isnull=True,
        swap_start__gt=now,
        notification_window_start__lte=now,
        notification_window_end__gte=now,
    )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_shift_swap_request(shift_swap_request_pk: int) -> None:
    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        logger.info(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return

    now = timezone.now()
    for user in shift_swap_request.possible_benefactors:
        if _should_notify_user(shift_swap_request, user, now):
            notify_user_about_shift_swap_request.delay(shift_swap_request.pk, user.pk)
            _mark_notified(shift_swap_request, user)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_about_shift_swap_request(shift_swap_request_pk: int, user_pk: int) -> None:
    # avoid circular import
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings

    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        logger.info(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.info(f"User {user_pk} does not exist")
        return

    device_to_notify = FCMDevice.get_active_device_for_user(user)
    if not device_to_notify:
        logger.info(f"FCMDevice does not exist for user {user_pk}")
        return

    try:
        mobile_app_user_settings = MobileAppUserSettings.objects.get(user=user)
    except MobileAppUserSettings.DoesNotExist:
        logger.info(f"MobileAppUserSettings does not exist for user {user_pk}")
        return

    if not mobile_app_user_settings.info_notifications_enabled:
        logger.info(f"Info notifications are not enabled for user {user_pk}")
        return

    message = _get_shift_swap_request_fcm_message(shift_swap_request, user, device_to_notify, mobile_app_user_settings)
    _send_push_notification(device_to_notify, message)


def _should_notify_user(shift_swap_request: ShiftSwapRequest, user: User, now: datetime.datetime) -> bool:
    from apps.mobile_app.models import MobileAppUserSettings

    try:
        mobile_app_user_settings = MobileAppUserSettings.objects.get(user=user)
    except MobileAppUserSettings.DoesNotExist:
        return False

    return (
        mobile_app_user_settings.info_notifications_enabled
        and user.is_in_working_hours(now, mobile_app_user_settings.time_zone)
        and not _already_notified(shift_swap_request, user)
    )


def _mark_notified(shift_swap_request: ShiftSwapRequest, user: User) -> None:
    key = _cache_key(shift_swap_request, user)
    cache.set(key, True, timeout=WINDOW.total_seconds())


def _already_notified(shift_swap_request: ShiftSwapRequest, user: User) -> bool:
    key = _cache_key(shift_swap_request, user)
    return cache.get(key) is True


def _cache_key(shift_swap_request: ShiftSwapRequest, user: User) -> str:
    return f"ssr_push:{shift_swap_request.pk}:{user.pk}"


def _get_shift_swap_request_fcm_message(shift_swap_request, user, device_to_notify, mobile_app_user_settings):
    from apps.mobile_app.models import MobileAppUserSettings

    thread_id = f"{shift_swap_request.public_primary_key}:{user.public_primary_key}:ssr"
    notification_title = "You have a new shift swap request"
    notification_subtitle = _get_shift_subtitle(
        shift_swap_request.schedule,
        shift_swap_request.swap_start,
        shift_swap_request.swap_end,
        mobile_app_user_settings,
    )

    data: FCMMessageData = {
        "title": notification_title,
        "subtitle": notification_subtitle,
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
            alert=ApsAlert(title=notification_title, subtitle=notification_subtitle),
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
