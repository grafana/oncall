from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.utils import timezone
from firebase_admin.messaging import Message

from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.tasks import (
    SSR_EARLIEST_NOTIFICATION_OFFSET,
    SSR_NOTIFICATION_WINDOW,
    _get_shift_swap_requests_to_notify,
    _has_user_been_notified_for_shift_swap_request,
    _mark_shift_swap_request_notified_for_user,
    _should_notify_user_about_shift_swap_request,
    notify_shift_swap_request,
    notify_shift_swap_requests,
    notify_user_about_shift_swap_request,
)
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb, ShiftSwapRequest
from apps.user_management.models import User
from apps.user_management.models.user import default_working_hours

MICROSECOND = timezone.timedelta(microseconds=1)


def test_window_more_than_24_hours():
    """
    SSR_NOTIFICATION_WINDOW must be more than one week, otherwise it's not possible to guarantee that the
    notification will be sent according to users' working hours. For example, if user only works on Fridays 10am-2pm,
    and a shift swap request is created on Friday 3pm, we must wait for a whole week to send the notification.
    """
    assert SSR_NOTIFICATION_WINDOW >= timezone.timedelta(weeks=1)


@pytest.mark.django_db
def test_get_shift_swap_requests_to_notify_starts_soon(
    make_organization, make_user, make_schedule, make_shift_swap_request
):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=10)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    assert _get_shift_swap_requests_to_notify(now - MICROSECOND) == []
    assert _get_shift_swap_requests_to_notify(now) == [shift_swap_request]
    assert _get_shift_swap_requests_to_notify(now + SSR_NOTIFICATION_WINDOW) == [shift_swap_request]
    assert _get_shift_swap_requests_to_notify(now + SSR_NOTIFICATION_WINDOW + MICROSECOND) == []


@pytest.mark.django_db
def test_get_shift_swap_requests_to_notify_starts_very_soon(
    make_organization, make_user, make_schedule, make_shift_swap_request
):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(minutes=1)
    swap_end = swap_start + timezone.timedelta(minutes=10)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    assert _get_shift_swap_requests_to_notify(now - MICROSECOND) == []
    assert _get_shift_swap_requests_to_notify(now) == [shift_swap_request]
    assert _get_shift_swap_requests_to_notify(now + timezone.timedelta(minutes=1)) == []


@pytest.mark.django_db
def test_get_shift_swap_requests_to_notify_starts_not_soon(
    make_organization, make_user, make_schedule, make_shift_swap_request
):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    assert _get_shift_swap_requests_to_notify(now) == []
    assert _get_shift_swap_requests_to_notify(swap_start - SSR_EARLIEST_NOTIFICATION_OFFSET - MICROSECOND) == []
    assert _get_shift_swap_requests_to_notify(swap_start - SSR_EARLIEST_NOTIFICATION_OFFSET) == [shift_swap_request]
    assert _get_shift_swap_requests_to_notify(
        swap_start - SSR_EARLIEST_NOTIFICATION_OFFSET + SSR_NOTIFICATION_WINDOW
    ) == [shift_swap_request]
    assert (
        _get_shift_swap_requests_to_notify(
            swap_start - SSR_EARLIEST_NOTIFICATION_OFFSET + SSR_NOTIFICATION_WINDOW + MICROSECOND
        )
        == []
    )


@pytest.mark.django_db
def test_notify_shift_swap_requests(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    with patch.object(notify_shift_swap_request, "delay") as mock_notify_shift_swap_request:
        with patch(
            "apps.mobile_app.tasks._get_shift_swap_requests_to_notify",
            return_value=ShiftSwapRequest.objects.filter(pk=shift_swap_request.pk),
        ) as mock_get_shift_swap_requests_to_notify:
            notify_shift_swap_requests()

    mock_get_shift_swap_requests_to_notify.assert_called_once()
    mock_notify_shift_swap_request.assert_called_once_with(shift_swap_request.pk)


@pytest.mark.django_db
def test_notify_shift_swap_request(make_organization, make_user, make_schedule, make_shift_swap_request, settings):
    organization = make_organization()
    user = make_user(organization=organization)
    other_user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    with patch.object(notify_user_about_shift_swap_request, "delay") as mock_notify_user_about_shift_swap_request:
        with patch("apps.mobile_app.tasks._should_notify_user_about_shift_swap_request", return_value=True):
            with patch.object(
                ShiftSwapRequest,
                "possible_benefactors",
                new_callable=PropertyMock(return_value=User.objects.filter(pk=other_user.pk)),
            ):
                notify_shift_swap_request(shift_swap_request.pk)

    mock_notify_user_about_shift_swap_request.assert_called_once_with(shift_swap_request.pk, other_user.pk)


@pytest.mark.django_db
def test_notify_shift_swap_request_should_not_notify_user(
    make_organization, make_user, make_schedule, make_shift_swap_request, settings
):
    organization = make_organization()
    user = make_user(organization=organization)
    other_user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    with patch.object(notify_user_about_shift_swap_request, "delay") as mock_notify_user_about_shift_swap_request:
        with patch("apps.mobile_app.tasks._should_notify_user_about_shift_swap_request", return_value=False):
            with patch.object(
                ShiftSwapRequest,
                "possible_benefactors",
                new_callable=PropertyMock(return_value=User.objects.filter(pk=other_user.pk)),
            ):
                notify_shift_swap_request(shift_swap_request.pk)

    mock_notify_user_about_shift_swap_request.assert_not_called()


@pytest.mark.django_db
def test_notify_shift_swap_request_success(
    make_organization, make_user, make_schedule, make_on_call_shift, make_shift_swap_request, settings
):
    organization = make_organization()
    beneficiary = make_user(organization=organization)

    # Set up the benefactor
    benefactor = make_user(
        organization=organization,
        working_hours={day: [{"start": "00:00:00", "end": "23:59:59"}] for day in default_working_hours().keys()},
    )
    MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=True)
    cache.clear()

    # Create schedule with the beneficiary and the benefactor in it
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    now = timezone.now()
    for user in [benefactor, beneficiary]:
        data = {
            "start": now - timezone.timedelta(days=1),
            "rotation_start": now - timezone.timedelta(days=1),
            "duration": timezone.timedelta(hours=1),
            "priority_level": 1,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    schedule.refresh_ical_file()
    schedule.refresh_from_db()

    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    with patch.object(notify_user_about_shift_swap_request, "delay") as mock_notify_user_about_shift_swap_request:
        notify_shift_swap_request(shift_swap_request.pk)

    mock_notify_user_about_shift_swap_request.assert_called_once_with(shift_swap_request.pk, benefactor.pk)


@pytest.mark.django_db
def test_notify_user_about_shift_swap_request(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    beneficiary = make_user(organization=organization, name="John Doe", username="john.doe")
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="Test Schedule")

    device_to_notify = FCMDevice.objects.create(user=benefactor, registration_id="test_device_id")
    MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=True)

    now = timezone.datetime(2023, 8, 1, 19, 38, tzinfo=timezone.utc)
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    with patch("apps.mobile_app.tasks._send_push_notification") as mock_send_push_notification:
        notify_user_about_shift_swap_request(shift_swap_request.pk, benefactor.pk)

    mock_send_push_notification.assert_called_once()
    assert mock_send_push_notification.call_args.args[0] == device_to_notify

    message: Message = mock_send_push_notification.call_args.args[1]
    assert message.data["type"] == "oncall.info"
    assert message.data["title"] == "New shift swap request"
    assert message.data["subtitle"] == "John Doe, Test Schedule"
    assert (
        message.data["route"]
        == f"/schedules/{schedule.public_primary_key}/ssrs/{shift_swap_request.public_primary_key}"
    )
    assert message.apns.payload.aps.sound.critical is False


@pytest.mark.django_db
def test_should_notify_user(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    beneficiary = make_user(organization=organization)
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    assert not MobileAppUserSettings.objects.exists()
    assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    mobile_app_settings = MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=False)
    assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    mobile_app_settings.info_notifications_enabled = True
    mobile_app_settings.save(update_fields=["info_notifications_enabled"])

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch("apps.mobile_app.tasks._has_user_been_notified_for_shift_swap_request", return_value=True):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=False):
        with patch("apps.mobile_app.tasks._has_user_been_notified_for_shift_swap_request", return_value=False):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch("apps.mobile_app.tasks._has_user_been_notified_for_shift_swap_request", return_value=False):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is True


@pytest.mark.django_db
def test_mark_notified(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    beneficiary = make_user(organization=organization)
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    cache.clear()
    assert _has_user_been_notified_for_shift_swap_request(shift_swap_request, benefactor) is False
    _mark_shift_swap_request_notified_for_user(shift_swap_request, benefactor)
    assert _has_user_been_notified_for_shift_swap_request(shift_swap_request, benefactor) is True

    with patch.object(cache, "set") as mock_cache_set:
        _mark_shift_swap_request_notified_for_user(shift_swap_request, benefactor)
        assert mock_cache_set.call_args.kwargs["timeout"] == SSR_NOTIFICATION_WINDOW.total_seconds()
