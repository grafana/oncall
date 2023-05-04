import typing
from unittest import mock

import pytest
from django.core.cache import cache
from django.utils import timezone
from fcm_django.models import FCMDevice

from apps.mobile_app import tasks
from apps.mobile_app.models import MobileAppUserSettings
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
    start_time: timezone.datetime, shift_pk: str, users: typing.List[ScheduleEventUser]
) -> ScheduleEvent:
    return {"start": start_time, "shift": {"pk": shift_pk}, "users": users}


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


@pytest.mark.parametrize(
    "info_notifications_enabled,now,going_oncall_notification_timing,schedule_start,expected",
    [
        # shift starts in 1h5m, user timing preference is 1h - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 10, 0),
            None,
        ),
        # shift starts in 1h4m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 9, 0),
            64 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 9, 0),
            None,
        ),
        # shift starts in 56m, user timing preference is 1h - send only if info_notifications_enabled is true
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 1, 0),
            56 * 60,
        ),
        (
            False,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 1, 0),
            None,
        ),
        # shift starts in 55m, user timing preference is 1h - don't send
        (
            True,
            timezone.datetime(2022, 5, 2, 12, 5, 0),
            ONE_HOUR_IN_SECONDS,
            timezone.datetime(2022, 5, 2, 13, 0, 0),
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
            now, user_mobile_settings, _create_schedule_event(schedule_start, "12345", [])
        )
        == expected
    )


def test_generate_going_oncall_push_notification_cache_key() -> None:
    user_pk = "adfad"
    schedule_event = {"shift": {"dfdfdf"}}
    time = "2023-05-04-11h"

    assert (
        tasks._generate_going_oncall_push_notification_cache_key(user_pk, schedule_event, time)
        == f"going_oncall_push_notification:{user_pk}:{schedule_event['shift']['pk']}:{time}"
    )


@mock.patch("apps.mobile_app.tasks._send_push_notification")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule_schedule_not_found(
    mocked_send_push_notification,
):
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule("cvnmcvnmcnvmcnvmncv")
    mocked_send_push_notification.assert_not_called()


@mock.patch("apps.mobile_app.tasks.OnCallSchedule.final_events")
@mock.patch("apps.mobile_app.tasks._send_push_notification")
@mock.patch("apps.mobile_app.tasks.should_we_send_going_oncall_push_notification")
@mock.patch("apps.mobile_app.tasks._get_youre_going_oncall_fcm_message")
@mock.patch("apps.mobile_app.tasks.timezone.now")
@pytest.mark.django_db
def test_conditionally_send_going_oncall_push_notifications_for_schedule(
    mock_timezone_now,
    mock_get_youre_going_oncall_fcm_message,
    mock_should_we_send_going_oncall_push_notification,
    mock_send_push_notification,
    mock_oncall_schedule_final_events,
    make_organization_and_user,
    make_schedule,
):
    timezone_now = timezone.datetime(2023, 5, 4, 10)
    mock_timezone_now.return_value = timezone_now

    organization, user = make_organization_and_user()

    shift_pk = "mncvmnvc"
    user_pk = user.public_primary_key
    mock_fcm_message = {"foo": "bar"}
    final_events = [
        _create_schedule_event(
            timezone.now(),
            shift_pk,
            [
                {
                    "pk": user_pk,
                },
            ],
        ),
    ]

    mock_get_youre_going_oncall_fcm_message.return_value = mock_fcm_message
    mock_should_we_send_going_oncall_push_notification.return_value = True
    mock_oncall_schedule_final_events.return_value = final_events

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    current_date_with_hour = timezone_now.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d-%Hh")
    cache_key = f"going_oncall_push_notification:{user_pk}:{shift_pk}:{current_date_with_hour}"

    assert cache.get(cache_key) is None

    # no device available
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    mock_send_push_notification.assert_not_called()

    # device available
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    MobileAppUserSettings.objects.create(user=user, going_oncall_notification_timing=ONCALL_TIMING_PREFERENCE)

    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)

    mock_get_youre_going_oncall_fcm_message.assert_called_once_with(user, schedule, device, ONCALL_TIMING_PREFERENCE)
    mock_send_push_notification.assert_called_once_with(device, mock_fcm_message)
    assert cache.get(cache_key) is True

    # we shouldn't double send the same push notification for the same user/shift within the same hour
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 1

    # we will resend the push notification for the same user/shift for a different hour
    mock_timezone_now.return_value = timezone_now + timezone.timedelta(hours=1)
    tasks.conditionally_send_going_oncall_push_notifications_for_schedule(schedule.pk)
    assert mock_send_push_notification.call_count == 2


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
