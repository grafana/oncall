import datetime
import json
import logging
import math
import typing

from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone
from firebase_admin.messaging import APNSPayload, Aps, ApsAlert, CriticalSound, Message

from apps.mobile_app.types import FCMMessageData, MessageType, Platform
from apps.mobile_app.utils import MAX_RETRIES, construct_fcm_message, send_push_notification
from apps.schedules.models import ShiftSwapRequest
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

if typing.TYPE_CHECKING:
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings


logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def _generate_cache_key(shift_swap_request: ShiftSwapRequest, user: User) -> str:
    return f"ssr_push:{shift_swap_request.pk}:{user.pk}"


def _mark_shift_swap_request_notified_for_user(shift_swap_request: ShiftSwapRequest, user: User, timeout: int) -> None:
    key = _generate_cache_key(shift_swap_request, user)
    cache.set(key, True, timeout=timeout)


def _get_shift_swap_requests_to_notify(now: datetime.datetime) -> list[tuple[ShiftSwapRequest, int]]:
    """
    Returns shifts swap requests that are open and are in the notification window.
    This method can return the same shift swap request multiple times while it's in the notification window,
    but users are only notified once per shift swap request (see _mark_shift_swap_request_notified_for_user).
    """

    shift_swap_requests_in_notification_window = []
    for shift_swap_request in ShiftSwapRequest.objects.get_open_requests(now):
        for idx, offset in enumerate(ShiftSwapRequest.FOLLOWUP_OFFSETS):
            next_offset = (
                ShiftSwapRequest.FOLLOWUP_OFFSETS[idx + 1]
                if idx + 1 < len(ShiftSwapRequest.FOLLOWUP_OFFSETS)
                else datetime.timedelta(0)
            )
            window = offset - next_offset - timezone.timedelta(microseconds=1)  # check SSRs up to the next offset

            notification_window_start = shift_swap_request.swap_start - offset
            notification_window_end = notification_window_start + window

            if notification_window_start <= now <= notification_window_end:
                next_notification_dt = shift_swap_request.swap_start - next_offset
                timeout = math.ceil((next_notification_dt - now).total_seconds())  # don't send notifications twice

                shift_swap_requests_in_notification_window.append((shift_swap_request, timeout))
                break

    return shift_swap_requests_in_notification_window


def _has_user_been_notified_for_shift_swap_request(shift_swap_request: ShiftSwapRequest, user: User) -> bool:
    key = _generate_cache_key(shift_swap_request, user)
    return cache.get(key) is True


def _should_notify_user_about_shift_swap_request(
    shift_swap_request: ShiftSwapRequest, user: User, now: datetime.datetime
) -> bool:
    # avoid circular import
    from apps.mobile_app.models import MobileAppUserSettings

    try:
        mobile_app_user_settings = MobileAppUserSettings.objects.get(user=user)
    except MobileAppUserSettings.DoesNotExist:
        return False  # don't notify if the app is not configured

    return user.is_in_working_hours(  # user must be in working hours
        now, mobile_app_user_settings.time_zone
    ) and not _has_user_been_notified_for_shift_swap_request(  # don't notify twice
        shift_swap_request, user
    )


def _get_notification_title_and_subtitle(shift_swap_request: ShiftSwapRequest) -> typing.Tuple[str, str]:
    notification_title: str
    notification_subtitle: str

    beneficiary_name = shift_swap_request.beneficiary.name or shift_swap_request.beneficiary.username
    schedule_name = shift_swap_request.schedule.name

    if shift_swap_request.is_taken:
        notification_title = "Your shift swap request has been taken"
        notification_subtitle = schedule_name
    else:
        notification_title = "New shift swap request"
        notification_subtitle = f"{beneficiary_name}, {schedule_name}"

    return (notification_title, notification_subtitle)


def _get_fcm_message(
    shift_swap_request: ShiftSwapRequest,
    user: User,
    device_to_notify: "FCMDevice",
    mobile_app_user_settings: "MobileAppUserSettings",
) -> Message:
    thread_id = f"{shift_swap_request.public_primary_key}:{user.public_primary_key}:ssr"

    notification_title, notification_subtitle = _get_notification_title_and_subtitle(shift_swap_request)

    # The mobile app will use this route to open the shift swap request
    route = f"/schedules/{shift_swap_request.schedule.public_primary_key}/ssrs/{shift_swap_request.public_primary_key}"

    data: FCMMessageData = {
        "title": notification_title,
        "subtitle": notification_subtitle,
        "route": route,
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


def _get_shift_swap_request(shift_swap_request_pk: int) -> typing.Optional[ShiftSwapRequest]:
    try:
        return ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        logger.info(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return


def _get_user_and_device(user_pk: int) -> typing.Optional[typing.Tuple[User, "FCMDevice", "MobileAppUserSettings"]]:
    # avoid circular import
    from apps.mobile_app.models import FCMDevice, MobileAppUserSettings

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

    return (user, device_to_notify, mobile_app_user_settings)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_about_shift_swap_request(shift_swap_request_pk: int, user_pk: int) -> None:
    """
    Send a push notification about a shift swap request to an individual user.
    """
    shift_swap_request = _get_shift_swap_request(shift_swap_request_pk)
    if not shift_swap_request:
        return

    user_and_device = _get_user_and_device(user_pk)
    if not user_and_device:
        return

    user, device_to_notify, mobile_app_user_settings = user_and_device

    if not shift_swap_request.is_open:
        logger.info(f"Shift swap request {shift_swap_request_pk} is not open anymore")
        return

    message = _get_fcm_message(shift_swap_request, user, device_to_notify, mobile_app_user_settings)
    send_push_notification(device_to_notify, message)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_shift_swap_request(shift_swap_request_pk: int, timeout: int) -> None:
    """
    Notify relevant users for an individual shift swap request.
    """
    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        logger.info(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return

    now = timezone.now()
    for user in shift_swap_request.possible_benefactors:
        if _should_notify_user_about_shift_swap_request(shift_swap_request, user, now):
            notify_user_about_shift_swap_request.delay(shift_swap_request.pk, user.pk)
            _mark_shift_swap_request_notified_for_user(shift_swap_request, user, timeout)


@shared_dedicated_queue_retry_task()
def notify_shift_swap_requests() -> None:
    """
    A periodic task that notifies users about shift swap requests.
    """
    for shift_swap_request, timeout in _get_shift_swap_requests_to_notify(timezone.now()):
        notify_shift_swap_request.delay(shift_swap_request.pk, timeout)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_beneficiary_about_taken_shift_swap_request(shift_swap_request_pk: int) -> None:
    shift_swap_request = _get_shift_swap_request(shift_swap_request_pk)
    if not shift_swap_request:
        return

    user_and_device = _get_user_and_device(shift_swap_request.beneficiary.pk)
    if not user_and_device:
        return

    user, device_to_notify, mobile_app_user_settings = user_and_device
    message = _get_fcm_message(shift_swap_request, user, device_to_notify, mobile_app_user_settings)
    send_push_notification(device_to_notify, message)
