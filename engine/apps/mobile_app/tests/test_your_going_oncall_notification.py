import json
import typing
from unittest import mock

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.mobile_app import tasks
from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.types import MessageType, Platform
from apps.schedules.models import OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.models.on_call_schedule import ScheduleEvent

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
    assert (
        tasks._shift_starts_within_range(timing_window_lower, timing_window_upper, seconds_until_shift_starts)
        == expected
    )


@pytest.mark.django_db
def test_get_youre_going_oncall_notification_title(make_organization_and_user, make_user, make_schedule):
    schedule_name = "asdfasdfasdfasdf"

    organization, user = make_organization_and_user()
    user2 = make_user(organization=organization)
    schedule = make_schedule(organization, name=schedule_name, schedule_class=OnCallScheduleWeb)
    shift_pk = "mncvmnvc"
    user_pk = user.public_primary_key
    user_locale = "fr_CA"
    seconds_until_going_oncall = 600
    humanized_time_until_going_oncall = "10 minutes"

    same_day_shift_start = timezone.datetime(2023, 7, 8, 9, 0, 0)
    same_day_shift_end = timezone.datetime(2023, 7, 8, 17, 0, 0)

    multiple_day_shift_start = timezone.datetime(2023, 7, 8, 9, 0, 0)
    multiple_day_shift_end = timezone.datetime(2023, 7, 12, 17, 0, 0)

    same_day_shift = _create_schedule_event(
        same_day_shift_start,
        same_day_shift_end,
        shift_pk,
        [
            {
                "pk": user_pk,
            },
        ],
    )

    multiple_day_shift = _create_schedule_event(
        multiple_day_shift_start,
        multiple_day_shift_end,
        shift_pk,
        [
            {
                "pk": user_pk,
            },
        ],
    )

    maus = MobileAppUserSettings.objects.create(user=user, locale=user_locale)
    maus_no_locale = MobileAppUserSettings.objects.create(user=user2)

    ##################
    # same day shift
    ##################
    same_day_shift_title = tasks._get_youre_going_oncall_notification_title(seconds_until_going_oncall)
    same_day_shift_subtitle = tasks._get_youre_going_oncall_notification_subtitle(schedule, same_day_shift, maus)
    same_day_shift_no_locale_subtitle = tasks._get_youre_going_oncall_notification_subtitle(
        schedule, same_day_shift, maus_no_locale
    )

    assert same_day_shift_title == f"Your on-call shift starts in {humanized_time_until_going_oncall}"
    assert same_day_shift_subtitle == f"09 h 00 - 17 h 00\nSchedule {schedule_name}"
    assert same_day_shift_no_locale_subtitle == f"9:00\u202fAM - 5:00\u202fPM\nSchedule {schedule_name}"

    ##################
    # multiple day shift
    ##################
    multiple_day_shift_title = tasks._get_youre_going_oncall_notification_title(seconds_until_going_oncall)
    multiple_day_shift_subtitle = tasks._get_youre_going_oncall_notification_subtitle(
        schedule, multiple_day_shift, maus
    )
    multiple_day_shift_no_locale_subtitle = tasks._get_youre_going_oncall_notification_subtitle(
        schedule, multiple_day_shift, maus_no_locale
    )

    assert multiple_day_shift_title == f"Your on-call shift starts in {humanized_time_until_going_oncall}"
    assert multiple_day_shift_subtitle == f"2023-07-08 09 h 00 - 2023-07-12 17 h 00\nSchedule {schedule_name}"
    assert (
        multiple_day_shift_no_locale_subtitle
        == f"7/8/23, 9:00\u202fAM - 7/12/23, 5:00\u202fPM\nSchedule {schedule_name}"
    )


@pytest.mark.parametrize(
    "user_timezone,expected_shift_times",
    [
        ("UTC", "9:00 AM - 5:00 PM"),
        ("Europe/Amsterdam", "11:00 AM - 7:00 PM"),
    ],
)
@pytest.mark.django_db
def test_get_youre_going_oncall_notification_subtitle(
    make_organization, make_user_for_organization, make_schedule, user_timezone, expected_shift_times
):
    schedule_name = "asdfasdfasdfasdf"

    organization = make_organization()
    user = make_user_for_organization(organization)
    user_pk = user.public_primary_key
    maus = MobileAppUserSettings.objects.create(user=user, time_zone=user_timezone)

    schedule = make_schedule(organization, name=schedule_name, schedule_class=OnCallScheduleWeb)

    shift_start = timezone.datetime(2023, 7, 8, 9, 0, 0)
    shift_end = timezone.datetime(2023, 7, 8, 17, 0, 0)

    shift = _create_schedule_event(
        shift_start,
        shift_end,
        "asdfasdfasdf",
        [
            {
                "pk": user_pk,
            },
        ],
    )

    assert (
        tasks._get_youre_going_oncall_notification_subtitle(schedule, shift, maus)
        == f"{expected_shift_times}\nSchedule {schedule_name}"
    )


@mock.patch("apps.mobile_app.tasks._get_youre_going_oncall_notification_subtitle")
@mock.patch("apps.mobile_app.tasks._get_youre_going_oncall_notification_title")
@mock.patch("apps.mobile_app.tasks._construct_fcm_message")
@mock.patch("apps.mobile_app.tasks.APNSPayload")
@mock.patch("apps.mobile_app.tasks.Aps")
@mock.patch("apps.mobile_app.tasks.ApsAlert")
@mock.patch("apps.mobile_app.tasks.CriticalSound")
@pytest.mark.django_db
def test_get_youre_going_oncall_fcm_message(
    mock_critical_sound,
    mock_aps_alert,
    mock_aps,
    mock_apns_payload,
    mock_construct_fcm_message,
    mock_get_youre_going_oncall_notification_title,
    mock_get_youre_going_oncall_notification_subtitle,
    make_organization,
    make_user_for_organization,
    make_schedule,
):
    mock_fcm_message = "mncvmnvcmnvcnmvcmncvmn"
    mock_notification_title = "asdfasdf"
    mock_notification_subtitle = "9:06\u202fAM - 9:06\u202fAM\nSchedule XYZ"
    shift_pk = "mncvmnvc"
    seconds_until_going_oncall = 600

    mock_construct_fcm_message.return_value = mock_fcm_message
    mock_get_youre_going_oncall_notification_title.return_value = mock_notification_title
    mock_get_youre_going_oncall_notification_subtitle.return_value = mock_notification_subtitle

    organization = make_organization()
    user_tz = "Europe/Amsterdam"
    user = make_user_for_organization(organization)
    user_pk = user.public_primary_key
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    notification_thread_id = f"{schedule.public_primary_key}:{user_pk}:going-oncall"

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
        "title": mock_notification_title,
        "subtitle": mock_notification_subtitle,
        "info_notification_sound_name": maus.get_notification_sound_name(MessageType.INFO, Platform.ANDROID),
        "info_notification_volume_type": maus.info_notification_volume_type,
        "info_notification_volume": str(maus.info_notification_volume),
        "info_notification_volume_override": json.dumps(maus.info_notification_volume_override),
    }

    fcm_message = tasks._get_youre_going_oncall_fcm_message(
        user, schedule, device, seconds_until_going_oncall, schedule_event
    )

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

    mock_get_youre_going_oncall_notification_subtitle.assert_called_once_with(schedule, schedule_event, maus)
    mock_get_youre_going_oncall_notification_title.assert_called_once_with(seconds_until_going_oncall)

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
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 13, 0),
            None,
        ),
        # shift starts in 1h7m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 12, 0),
            None,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 12, 0),
            None,
        ),
        # shift starts in 53m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 58, 0),
            None,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 58, 0),
            None,
        ),
        # shift starts in 52m, user timing preference is 1h - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 57, 0),
            None,
        ),
        # shift starts in 16m, don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 21, 0),
            None,
        ),
        # shift starts in 15m - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 20, 0),
            15 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 20, 0),
            None,
        ),
        # shift starts in 0secs - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            0,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            None,
        ),
        # shift started 5secs ago - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 12, 4, 55),
            None,
        ),
    ],
)
@pytest.mark.django_db
def test_should_we_send_going_oncall_push_notification(
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
        tasks.should_we_send_going_oncall_push_notification(
            now, user_mobile_settings, _create_schedule_event(schedule_start, schedule_start, "12345", [])
        )
        == expected
    )


def test_generate_going_oncall_push_notification_cache_key() -> None:
    user_pk = "adfad"
    schedule_event = {"shift": {"pk": "dfdfdf"}}

    assert (
        tasks._generate_going_oncall_push_notification_cache_key(user_pk, schedule_event)
        == f"going_oncall_push_notification:{user_pk}:{schedule_event['shift']['pk']}"
    )


@mock.patch("apps.mobile_app.tasks._send_push_notification")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule_schedule_not_found(
    mocked_send_push_notification,
):
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(12345)
    mocked_send_push_notification.assert_not_called()


@mock.patch("apps.mobile_app.tasks.OnCallSchedule.final_events")
@mock.patch("apps.mobile_app.tasks._send_push_notification")
@mock.patch("apps.mobile_app.tasks.should_we_send_going_oncall_push_notification")
@mock.patch("apps.mobile_app.tasks._get_youre_going_oncall_fcm_message")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule(
    mock_get_youre_going_oncall_fcm_message,
    mock_should_we_send_going_oncall_push_notification,
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
    mock_get_youre_going_oncall_fcm_message.return_value = mock_fcm_message
    mock_should_we_send_going_oncall_push_notification.return_value = seconds_until_shift_starts
    mock_oncall_schedule_final_events.return_value = final_events

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    cache_key = f"going_oncall_push_notification:{user_pk}:{shift_pk}"

    assert cache.get(cache_key) is None

    # no device available
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    mock_send_push_notification.assert_not_called()

    # device available
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    MobileAppUserSettings.objects.create(user=user, going_oncall_notification_timing=ONCALL_TIMING_PREFERENCE)

    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)

    mock_get_youre_going_oncall_fcm_message.assert_called_once_with(
        user, schedule, device, seconds_until_shift_starts, schedule_event
    )
    mock_send_push_notification.assert_called_once_with(device, mock_fcm_message)
    assert cache.get(cache_key) is True

    # we shouldn't double send the same push notification for the same user/shift
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 1

    # if the cache key expires we will resend the push notification for the same user/shift
    # (in reality we're setting a timeout on the cache key, here we will just delete it to simulate this)
    cache.delete(cache_key)

    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 2
    assert cache.get(cache_key) is True


@mock.patch("apps.mobile_app.tasks.conditionally_send_going_oncall_push_notifications_for_schedule")
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

    tasks.conditionally_send_going_oncall_push_notifications_for_all_schedules()

    mocked_conditionally_send_going_oncall_push_notifications_for_schedule.apply_async.assert_has_calls(
        [
            mock.call((schedule1.pk,)),
            mock.call((schedule2.pk,)),
            mock.call((schedule3.pk,)),
        ],
        any_order=True,
    )
