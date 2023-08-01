from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.utils import timezone
from firebase_admin.messaging import Message

from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.tasks import (
    EARLIEST_NOTIFICATION_OFFSET,
    WINDOW,
    MessageType,
    _already_notified,
    _get_shift_swap_requests_to_notify,
    _mark_notified,
    _should_notify_user,
    notify_shift_swap_request,
    notify_shift_swap_requests,
    notify_user_about_shift_swap_request,
)
from apps.schedules.models import OnCallScheduleWeb, ShiftSwapRequest
from apps.user_management.models import User

MICROSECOND = timezone.timedelta(microseconds=1)


def test_window_more_than_24_hours():
    assert WINDOW >= timezone.timedelta(hours=24)


@pytest.mark.django_db
def test_get_shift_swap_requests_to_notify_starts_soon(
    make_organization, make_user, make_schedule, make_shift_swap_request
):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=7)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    assert list(_get_shift_swap_requests_to_notify(now - MICROSECOND)) == []
    assert list(_get_shift_swap_requests_to_notify(now)) == [shift_swap_request]
    assert list(_get_shift_swap_requests_to_notify(now + WINDOW)) == [shift_swap_request]
    assert list(_get_shift_swap_requests_to_notify(now + WINDOW + MICROSECOND)) == []


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

    assert list(_get_shift_swap_requests_to_notify(now - MICROSECOND)) == []
    assert list(_get_shift_swap_requests_to_notify(now)) == [shift_swap_request]
    assert list(_get_shift_swap_requests_to_notify(now + timezone.timedelta(minutes=1))) == []


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

    assert list(_get_shift_swap_requests_to_notify(now)) == []
    assert list(_get_shift_swap_requests_to_notify(swap_start - EARLIEST_NOTIFICATION_OFFSET - MICROSECOND)) == []
    assert list(_get_shift_swap_requests_to_notify(swap_start - EARLIEST_NOTIFICATION_OFFSET)) == [shift_swap_request]
    assert list(_get_shift_swap_requests_to_notify(swap_start - EARLIEST_NOTIFICATION_OFFSET + WINDOW)) == [
        shift_swap_request
    ]
    assert (
        list(_get_shift_swap_requests_to_notify(swap_start - EARLIEST_NOTIFICATION_OFFSET + WINDOW + MICROSECOND)) == []
    )


@pytest.mark.django_db
def test_notify_shift_swap_requests(make_organization, make_user, make_schedule, make_shift_swap_request, settings):
    settings.FEATURE_SHIFT_SWAPS_ENABLED = True

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
def test_notify_shift_swap_requests_feature_flag_disabled(
    make_organization, make_user, make_schedule, make_shift_swap_request, settings
):
    settings.FEATURE_SHIFT_SWAPS_ENABLED = False
    with patch("apps.mobile_app.tasks._get_shift_swap_requests_to_notify") as mock_get_shift_swap_requests_to_notify:
        notify_shift_swap_requests()

    mock_get_shift_swap_requests_to_notify.assert_not_called()


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
        with patch("apps.mobile_app.tasks._should_notify_user", return_value=True):
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
        with patch("apps.mobile_app.tasks._should_notify_user", return_value=False):
            with patch.object(
                ShiftSwapRequest,
                "possible_benefactors",
                new_callable=PropertyMock(return_value=User.objects.filter(pk=other_user.pk)),
            ):
                notify_shift_swap_request(shift_swap_request.pk)

    mock_notify_user_about_shift_swap_request.assert_not_called()


@pytest.mark.django_db
def test_notify_user_about_shift_swap_request(
    make_organization, make_user, make_schedule, make_shift_swap_request, settings
):
    organization = make_organization()
    beneficiary = make_user(organization=organization)
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="Test")

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
    assert message.data["type"] == MessageType.INFO
    assert message.data["title"] == "You have a new shift swap request"
    assert message.data["subtitle"] == "11/9/23, 7:38\u202fPM - 11/10/23, 7:38\u202fPM\nSchedule Test"
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
    assert _should_notify_user(shift_swap_request, benefactor, now) is False

    MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=True)
    assert _should_notify_user(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch("apps.mobile_app.tasks._already_notified", return_value=True):
            assert _should_notify_user(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=False):
        with patch("apps.mobile_app.tasks._already_notified", return_value=False):
            assert _should_notify_user(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch("apps.mobile_app.tasks._already_notified", return_value=False):
            assert _should_notify_user(shift_swap_request, benefactor, now) is True


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
    assert _already_notified(shift_swap_request, benefactor) is False
    _mark_notified(shift_swap_request, benefactor)
    assert _already_notified(shift_swap_request, benefactor) is True

    with patch.object(cache, "set") as mock_cache_set:
        _mark_notified(shift_swap_request, benefactor)
        assert mock_cache_set.call_args.kwargs["timeout"] == WINDOW.total_seconds()
