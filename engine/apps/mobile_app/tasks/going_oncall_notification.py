import datetime
import json
import logging
import math
import typing

import humanize
import pytz
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone
from firebase_admin.messaging import APNSPayload, Aps, ApsAlert, CriticalSound, Message

from apps.mobile_app.types import FCMMessageData, MessageType, Platform
from apps.mobile_app.utils import MAX_RETRIES, construct_fcm_message, send_push_notification
from apps.schedules.models.on_call_schedule import OnCallSchedule, ScheduleEvent
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.l10n import format_localized_datetime, format_localized_time

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings


logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def _get_notification_title(seconds_until_going_oncall: int) -> str:
    return f"Your on-call shift starts in {humanize.naturaldelta(seconds_until_going_oncall)}"


def _get_notification_subtitle(
    schedule: OnCallSchedule,
    schedule_event: ScheduleEvent,
    mobile_app_user_settings: "MobileAppUserSettings",
) -> str:
    shift_start = schedule_event["start"]
    shift_end = schedule_event["end"]
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


def _get_fcm_message(
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
    notification_title = _get_notification_title(seconds_until_going_oncall)
    notification_subtitle = _get_notification_subtitle(schedule, schedule_event, mobile_app_user_settings)

    data: FCMMessageData = {
        "title": notification_title,
        "subtitle": notification_subtitle,
        "info_notification_sound_name": mobile_app_user_settings.get_notification_sound_name(
            MessageType.INFO, Platform.ANDROID
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
                name=mobile_app_user_settings.get_notification_sound_name(MessageType.INFO, Platform.IOS),
            ),
            custom_data={
                "interruption-level": "time-sensitive",
            },
        ),
    )

    return construct_fcm_message(MessageType.INFO, device_to_notify, thread_id, data, apns_payload)


def _shift_starts_within_range(
    timing_window_lower: int, timing_window_upper: int, seconds_until_shift_starts: int
) -> bool:
    return timing_window_lower <= seconds_until_shift_starts <= timing_window_upper


def _should_we_send_push_notification(
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


def _generate_cache_key(user_pk: str, schedule_event: ScheduleEvent) -> str:
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
        _generate_cache_key(user["pk"], schedule_event)
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

            cache_key = _generate_cache_key(user_pk, schedule_event)
            already_sent_this_push_notification = cache_key in relevant_notifications_already_sent
            seconds_until_going_oncall = _should_we_send_push_notification(
                now, mobile_app_user_settings, schedule_event
            )

            if seconds_until_going_oncall is not None and not already_sent_this_push_notification:
                message = _get_fcm_message(user, schedule, device_to_notify, seconds_until_going_oncall, schedule_event)
                send_push_notification(device_to_notify, message)
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
