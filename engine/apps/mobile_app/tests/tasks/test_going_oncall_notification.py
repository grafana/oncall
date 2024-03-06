import json
import typing
from unittest import mock

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.tasks.going_oncall_notification import (
    _generate_cache_key,
    _get_fcm_message,
    _get_notification_subtitle,
    _get_notification_title,
    _shift_starts_within_range,
    _should_we_send_push_notification,
    conditionally_send_going_oncall_push_notifications_for_all_schedules,
    conditionally_send_going_oncall_push_notifications_for_schedule,
)
from apps.mobile_app.types import MessageType, Platform
from apps.mobile_app.utils import add_stack_slug_to_message_title
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.models.on_call_schedule import ScheduleEvent

FIFTEEN_MINUTES_IN_SECONDS = 15 * 60
ONE_HOUR_IN_SECONDS = 60 * 60
ONCALL_TIMING_PREFERENCE = ONE_HOUR_IN_SECONDS * 12


class ScheduleEventUser(typing.TypedDict):
    pk: str


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


def _create_schedule_event(
    start_time: timezone.datetime, end_time: timezone.datetime, shift_pk: str, users: typing.List[ScheduleEventUser]
) -> ScheduleEvent:
    return {"start": start_time, "end": end_time, "shift": {"pk": shift_pk}, "users": users}


@pytest.mark.parametrize(
    "timing_window_lower,timing_window_upper,seconds_until_shift_starts,expected",
    [
        (0, 15 * 60, 0, True),
        (0, 15 * 60, 1, True),
        (0, 15 * 60, (15 * 60) - 1, True),
        (0, 15 * 60, 15 * 60, True),
    ],
)
@pytest.mark.django_db
def test_shift_starts_within_range(timing_window_lower, timing_window_upper, seconds_until_shift_starts, expected):
    assert _shift_starts_within_range(timing_window_lower, timing_window_upper, seconds_until_shift_starts) == expected


@pytest.mark.parametrize(
    "seconds_until_going_oncall,humanized_time_until_going_oncall",
    [
        (8 * 60, "15 minutes"),  # 8 minutes
        (600, "15 minutes"),
        ((60 * 60 * 11) + (53 * 60), "12 hours"),  # 11 hours and 53 minutes
        ((60 * 60 * 12) + (10 * 60), "12 hours"),  # 12 hours and 10 minutes
        (60 * 60 * 26, "a day"),  # 1 day and 2 hours
    ],
)
@pytest.mark.django_db
def test_get_notification_title(seconds_until_going_oncall, humanized_time_until_going_oncall):
    assert (
        _get_notification_title(seconds_until_going_oncall)
        == f"Your on-call shift starts in {humanized_time_until_going_oncall}"
    )


@pytest.mark.parametrize(
    "user_timezone,shift_start_time,shift_end_time,expected",
    [
        # same day shift
        ("UTC", timezone.datetime(2023, 7, 8, 9, 0, 0), timezone.datetime(2023, 7, 8, 17, 0, 0), "9:00 AM - 5:00 PM"),
        (
            "Europe/Amsterdam",
            timezone.datetime(2023, 7, 8, 9, 0, 0),
            timezone.datetime(2023, 7, 8, 17, 0, 0),
            "11:00 AM - 7:00 PM",
        ),
        # multi-day shift
        (
            "UTC",
            timezone.datetime(2023, 7, 8, 9, 0, 0),
            timezone.datetime(2023, 7, 12, 17, 0, 0),
            "7/8/23, 9:00 AM - 7/12/23, 5:00 PM",
        ),
        (
            "Europe/Amsterdam",
            timezone.datetime(2023, 7, 8, 9, 0, 0),
            timezone.datetime(2023, 7, 12, 17, 0, 0),
            "7/8/23, 11:00 AM - 7/12/23, 7:00 PM",
        ),
    ],
)
@pytest.mark.django_db
def test_get_notification_subtitle(
    make_organization,
    make_user_for_organization,
    make_schedule,
    user_timezone,
    shift_start_time,
    shift_end_time,
    expected,
):
    schedule_name = "asdfasdfasdfasdf"

    organization = make_organization()
    user = make_user_for_organization(organization)
    user_pk = user.public_primary_key
    maus = MobileAppUserSettings.objects.create(user=user, time_zone=user_timezone)
    schedule = make_schedule(organization, name=schedule_name, schedule_class=OnCallScheduleWeb)

    shift = _create_schedule_event(
        shift_start_time,
        shift_end_time,
        "asdfasdfasdf",
        [
            {
                "pk": user_pk,
            },
        ],
    )

    assert _get_notification_subtitle(schedule, shift, maus) == f"{expected}\nSchedule {schedule_name}"


@pytest.mark.parametrize(
    "shift_start_time,shift_end_time,expected",
    [
        # same day shift
        (timezone.datetime(2023, 7, 8, 9, 0, 0), timezone.datetime(2023, 7, 8, 17, 0, 0), "9:00 AM - 5:00 PM"),
        # multi-day shift
        (
            timezone.datetime(2023, 7, 8, 9, 0, 0),
            timezone.datetime(2023, 7, 12, 17, 0, 0),
            "7/8/23, 9:00 AM - 7/12/23, 5:00 PM",
        ),
    ],
)
@pytest.mark.django_db
def test_get_notification_subtitle_no_locale(
    make_organization,
    make_user_for_organization,
    make_schedule,
    shift_start_time,
    shift_end_time,
    expected,
):
    schedule_name = "asdfasdfasdfasdf"

    organization = make_organization()
    user = make_user_for_organization(organization)
    user_pk = user.public_primary_key
    maus = MobileAppUserSettings.objects.create(user=user)
    schedule = make_schedule(organization, name=schedule_name, schedule_class=OnCallScheduleWeb)

    shift = _create_schedule_event(
        shift_start_time,
        shift_end_time,
        "asdfasdfasdf",
        [
            {
                "pk": user_pk,
            },
        ],
    )

    assert _get_notification_subtitle(schedule, shift, maus) == f"{expected}\nSchedule {schedule_name}"


@mock.patch("apps.mobile_app.tasks.going_oncall_notification._get_notification_subtitle")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification._get_notification_title")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.construct_fcm_message")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.APNSPayload")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.Aps")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.ApsAlert")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.CriticalSound")
@pytest.mark.django_db
def test_get_fcm_message(
    mock_critical_sound,
    mock_aps_alert,
    mock_aps,
    mock_apns_payload,
    mock_construct_fcm_message,
    mock_get_notification_title,
    mock_get_notification_subtitle,
    make_organization,
    make_user_for_organization,
    make_schedule,
):
    organization = make_organization()
    user_tz = "Europe/Amsterdam"
    user = make_user_for_organization(organization)
    user_pk = user.public_primary_key
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    notification_thread_id = f"{schedule.public_primary_key}:{user_pk}:going-oncall"

    mock_fcm_message = "mncvmnvcmnvcnmvcmncvmn"
    mock_notification_title = "asdfasdf"
    mock_notification_subtitle = "9:06\u202fAM - 9:06\u202fAM\nSchedule XYZ"
    shift_pk = "mncvmnvc"
    seconds_until_going_oncall = 600

    mock_construct_fcm_message.return_value = mock_fcm_message
    mock_get_notification_title.return_value = mock_notification_title
    mock_get_notification_subtitle.return_value = mock_notification_subtitle

    schedule_event = _create_schedule_event(
        timezone.now(),
        timezone.now(),
        shift_pk,
        [
            {
                "pk": user_pk,
            },
        ],
    )

    device = FCMDevice.objects.create(user=user)
    maus = MobileAppUserSettings.objects.create(user=user, time_zone=user_tz)

    data = {
        "title": add_stack_slug_to_message_title(mock_notification_title, organization),
        "subtitle": mock_notification_subtitle,
        "orgName": organization.stack_slug,
        "info_notification_sound_name": maus.get_notification_sound_name(MessageType.INFO, Platform.ANDROID),
        "info_notification_volume_type": maus.info_notification_volume_type,
        "info_notification_volume": str(maus.info_notification_volume),
        "info_notification_volume_override": json.dumps(maus.info_notification_volume_override),
    }

    fcm_message = _get_fcm_message(user, schedule, device, seconds_until_going_oncall, schedule_event)

    assert fcm_message == mock_fcm_message

    mock_aps_alert.assert_called_once_with(title=mock_notification_title, subtitle=mock_notification_subtitle)
    mock_critical_sound.assert_called_once_with(
        critical=False, name=maus.get_notification_sound_name(MessageType.INFO, Platform.IOS)
    )
    mock_aps.assert_called_once_with(
        thread_id=notification_thread_id,
        alert=mock_aps_alert.return_value,
        sound=mock_critical_sound.return_value,
        custom_data={
            "interruption-level": "time-sensitive",
        },
    )
    mock_apns_payload.assert_called_once_with(aps=mock_aps.return_value)

    mock_get_notification_subtitle.assert_called_once_with(schedule, schedule_event, maus)
    mock_get_notification_title.assert_called_once_with(seconds_until_going_oncall)

    mock_construct_fcm_message.assert_called_once_with(
        MessageType.INFO, device, notification_thread_id, data, mock_apns_payload.return_value
    )


@pytest.mark.parametrize(
    "info_notifications_enabled,now,going_oncall_notification_timing,schedule_start,expected",
    [
        # shift starts in 1h8m, user timing preference is 1h - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 13, 13, 0),
            None,
        ),
        # shift starts in 1h7m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 13, 12, 0),
            67 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 13, 12, 0),
            None,
        ),
        # shift starts in 53m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 58, 0),
            53 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 58, 0),
            None,
        ),
        # shift starts in 52m, user timing preference is 1h - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 57, 0),
            None,
        ),
        # shift starts in 16m, don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 21, 0),
            None,
        ),
        # shift starts in 15m, user timing preference is 1h and 15m - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS, FIFTEEN_MINUTES_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 20, 0),
            15 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS, FIFTEEN_MINUTES_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 20, 0),
            None,
        ),
        # shift starts in 0secs - don't send
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            None,
        ),
        # shift started 5secs ago - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            [ONE_HOUR_IN_SECONDS],
            timezone.datetime(2022, 5, 2, 12, 4, 55),
            None,
        ),
    ],
)
@pytest.mark.django_db
def test_should_we_send_push_notification(
    make_organization_and_user,
    info_notifications_enabled,
    now,
    going_oncall_notification_timing,
    schedule_start,
    expected,
):
    _, user = make_organization_and_user()
    user_mobile_settings = MobileAppUserSettings.objects.create(
        user=user,
        info_notifications_enabled=info_notifications_enabled,
        going_oncall_notification_timing=going_oncall_notification_timing,
    )

    assert (
        _should_we_send_push_notification(
            now, user_mobile_settings, _create_schedule_event(schedule_start, schedule_start, "12345", [])
        )
        == expected
    )


def test_generate_cache_key() -> None:
    user_pk = "adfad"
    schedule_event = {"shift": {"pk": "dfdfdf"}}

    assert (
        _generate_cache_key(user_pk, schedule_event)
        == f"going_oncall_push_notification:{user_pk}:{schedule_event['shift']['pk']}"
    )


@mock.patch("apps.mobile_app.tasks.going_oncall_notification.send_push_notification")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule_schedule_not_found(
    mocked_send_push_notification,
):
    conditionally_send_going_oncall_push_notifications_for_schedule(12345)
    mocked_send_push_notification.assert_not_called()


@mock.patch("apps.mobile_app.tasks.going_oncall_notification.OnCallSchedule.final_events")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification.send_push_notification")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification._should_we_send_push_notification")
@mock.patch("apps.mobile_app.tasks.going_oncall_notification._get_fcm_message")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule(
    mock_get_fcm_message,
    mock_should_we_send_push_notification,
    mock_send_push_notification,
    mock_oncall_schedule_final_events,
    make_organization_and_user,
    make_schedule,
):
    organization, user = make_organization_and_user()

    shift_pk = "mncvmnvc"
    user_pk = user.public_primary_key
    mock_fcm_message = {"foo": "bar"}

    schedule_event = _create_schedule_event(
        timezone.now(),
        timezone.now(),
        shift_pk,
        [
            {
                "pk": user_pk,
            },
        ],
    )
    final_events = [schedule_event]

    seconds_until_shift_starts = 58989
    mock_get_fcm_message.return_value = mock_fcm_message
    mock_should_we_send_push_notification.return_value = seconds_until_shift_starts
    mock_oncall_schedule_final_events.return_value = final_events

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    cache_key = f"going_oncall_push_notification:{user_pk}:{shift_pk}"

    assert cache.get(cache_key) is None

    # no device available
    conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    mock_send_push_notification.assert_not_called()

    # device available
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    MobileAppUserSettings.objects.create(user=user, going_oncall_notification_timing=ONCALL_TIMING_PREFERENCE)

    conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)

    mock_get_fcm_message.assert_called_once_with(user, schedule, device, seconds_until_shift_starts, schedule_event)
    mock_send_push_notification.assert_called_once_with(device, mock_fcm_message)
    assert cache.get(cache_key) is True

    # we shouldn't double send the same push notification for the same user/shift
    conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 1

    # if the cache key expires we will resend the push notification for the same user/shift
    # (in reality we're setting a timeout on the cache key, here we will just delete it to simulate this)
    cache.delete(cache_key)

    conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 2
    assert cache.get(cache_key) is True


@mock.patch(
    "apps.mobile_app.tasks.going_oncall_notification.conditionally_send_going_oncall_push_notifications_for_schedule"
)
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_all_schedules(
    mocked_conditionally_send_going_oncall_push_notifications_for_schedule,
    make_organization_and_user,
    make_schedule,
):
    organization, _ = make_organization_and_user()
    schedule1 = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule2 = make_schedule(organization, schedule_class=OnCallScheduleICal)
    schedule3 = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    conditionally_send_going_oncall_push_notifications_for_all_schedules()

    mocked_conditionally_send_going_oncall_push_notifications_for_schedule.apply_async.assert_has_calls(
        [
            mock.call((schedule1.pk,)),
            mock.call((schedule2.pk,)),
            mock.call((schedule3.pk,)),
        ],
        any_order=True,
    )
