from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.utils import timezone
from firebase_admin.messaging import Message

from apps.mobile_app.models import FCMDevice, MobileAppUserSettings
from apps.mobile_app.tasks.new_shift_swap_request import (
    _get_notification_title_and_subtitle,
    _get_shift_swap_request,
    _get_shift_swap_requests_to_notify,
    _get_user_and_device,
    _has_user_been_notified_for_shift_swap_request,
    _mark_shift_swap_request_notified_for_user,
    _should_notify_user_about_shift_swap_request,
    notify_beneficiary_about_taken_shift_swap_request,
    notify_shift_swap_request,
    notify_shift_swap_requests,
    notify_user_about_shift_swap_request,
)
from apps.mobile_app.utils import add_stack_slug_to_message_title
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb, ShiftSwapRequest
from apps.user_management.models import User
from apps.user_management.models.user import default_working_hours

MICROSECOND = timezone.timedelta(microseconds=1)
TIMEOUT = 123


@pytest.mark.django_db
def test_get_shift_swap_requests_to_notify(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    user = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    swap_start = timezone.now()
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, user, swap_start=swap_start, swap_end=swap_end, created_at=swap_start - timezone.timedelta(days=27)
    )

    def _timeout(**kwargs):
        return int(timezone.timedelta(**kwargs).total_seconds())

    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=28, microseconds=1)) == []
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=28)) == [
        (shift_swap_request, _timeout(days=7))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=27)) == [
        (shift_swap_request, _timeout(days=6))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=21)) == [
        (shift_swap_request, _timeout(days=7))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=14)) == [
        (shift_swap_request, _timeout(days=7))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=10)) == [
        (shift_swap_request, _timeout(days=3))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=7)) == [
        (shift_swap_request, _timeout(days=4))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=3)) == [
        (shift_swap_request, _timeout(days=1))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=2)) == [
        (shift_swap_request, _timeout(days=1))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(days=1)) == [
        (shift_swap_request, _timeout(hours=12))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(hours=18)) == [
        (shift_swap_request, _timeout(hours=6))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(hours=12)) == [
        (shift_swap_request, _timeout(hours=12))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(hours=11)) == [
        (shift_swap_request, _timeout(hours=11))
    ]
    assert _get_shift_swap_requests_to_notify(swap_start - timezone.timedelta(seconds=1)) == [
        (shift_swap_request, _timeout(seconds=1))
    ]
    # check that the timeout is ceil-ed to the next second
    assert _get_shift_swap_requests_to_notify(
        swap_start - timezone.timedelta(seconds=1) + timezone.timedelta(milliseconds=600)
    ) == [(shift_swap_request, _timeout(seconds=1))]
    assert _get_shift_swap_requests_to_notify(swap_start) == []


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
            "apps.mobile_app.tasks.new_shift_swap_request._get_shift_swap_requests_to_notify",
            return_value=[(ShiftSwapRequest.objects.filter(pk=shift_swap_request.pk).first(), TIMEOUT)],
        ) as mock_get_shift_swap_requests_to_notify:
            notify_shift_swap_requests()

    mock_get_shift_swap_requests_to_notify.assert_called_once()
    mock_notify_shift_swap_request.assert_called_once_with(shift_swap_request.pk, TIMEOUT)


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
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._should_notify_user_about_shift_swap_request",
            return_value=True,
        ):
            with patch.object(
                ShiftSwapRequest,
                "possible_benefactors",
                new_callable=PropertyMock(return_value=User.objects.filter(pk=other_user.pk)),
            ):
                notify_shift_swap_request(shift_swap_request.pk, TIMEOUT)

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
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._should_notify_user_about_shift_swap_request",
            return_value=False,
        ):
            with patch.object(
                ShiftSwapRequest,
                "possible_benefactors",
                new_callable=PropertyMock(return_value=User.objects.filter(pk=other_user.pk)),
            ):
                notify_shift_swap_request(shift_swap_request.pk, TIMEOUT)

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
        notify_shift_swap_request(shift_swap_request.pk, TIMEOUT)

    mock_notify_user_about_shift_swap_request.assert_called_once_with(shift_swap_request.pk, benefactor.pk)


@patch("apps.mobile_app.tasks.new_shift_swap_request._get_user_and_device")
@patch("apps.mobile_app.tasks.new_shift_swap_request.send_push_notification")
@pytest.mark.django_db
def test_notify_user_about_shift_swap_request(
    mock_send_push_notification,
    mock_get_user_and_device,
    make_organization,
    make_user,
    make_schedule,
    make_shift_swap_request,
):
    organization = make_organization()
    beneficiary = make_user(organization=organization, name="John Doe", username="john.doe")
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="Test Schedule")

    device_to_notify = FCMDevice.objects.create(user=benefactor, registration_id="test_device_id")
    maus = MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=True)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    mock_get_user_and_device.return_value = None
    notify_user_about_shift_swap_request(shift_swap_request.pk, benefactor.pk)
    mock_get_user_and_device.assert_called_once_with(benefactor.pk)
    mock_send_push_notification.assert_not_called()

    mock_get_user_and_device.reset_mock()

    mock_get_user_and_device.return_value = (benefactor, device_to_notify, maus)
    notify_user_about_shift_swap_request(shift_swap_request.pk, benefactor.pk)
    mock_get_user_and_device.assert_called_once_with(benefactor.pk)
    mock_send_push_notification.assert_called_once()

    assert mock_send_push_notification.call_args.args[0] == device_to_notify

    message: Message = mock_send_push_notification.call_args.args[1]
    assert message.data["type"] == "oncall.info"
    assert message.data["title"] == add_stack_slug_to_message_title("New shift swap request", organization)
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

    # check _should_notify_user_about_shift_swap_request is True when info notifications are disabled
    mobile_app_settings = MobileAppUserSettings.objects.create(user=benefactor, info_notifications_enabled=False)
    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._has_user_been_notified_for_shift_swap_request",
            return_value=False,
        ):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is True

    mobile_app_settings.info_notifications_enabled = True
    mobile_app_settings.save(update_fields=["info_notifications_enabled"])

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._has_user_been_notified_for_shift_swap_request",
            return_value=True,
        ):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=False):
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._has_user_been_notified_for_shift_swap_request",
            return_value=False,
        ):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is False

    with patch.object(benefactor, "is_in_working_hours", return_value=True):
        with patch(
            "apps.mobile_app.tasks.new_shift_swap_request._has_user_been_notified_for_shift_swap_request",
            return_value=False,
        ):
            assert _should_notify_user_about_shift_swap_request(shift_swap_request, benefactor, now) is True


@pytest.mark.django_db
def test_get_notification_title_and_subtitle(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    beneficiary_name = "hello"
    beneficiary = make_user(organization=organization, name=beneficiary_name)
    benefactor = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    ssr = make_shift_swap_request(schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now)

    title, subtitle = _get_notification_title_and_subtitle(ssr)
    assert title == "New shift swap request"
    assert subtitle == f"{beneficiary_name}, {schedule.name}"

    ssr.benefactor = benefactor
    ssr.save()
    ssr.refresh_from_db()

    title, subtitle = _get_notification_title_and_subtitle(ssr)
    assert title == "Your shift swap request has been taken"
    assert subtitle == schedule.name


@pytest.mark.django_db
def test_get_shift_swap_request(make_organization, make_user, make_schedule, make_shift_swap_request):
    organization = make_organization()
    beneficiary = make_user(organization=organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    ssr = make_shift_swap_request(schedule, beneficiary, swap_start=swap_start, swap_end=swap_end, created_at=now)

    assert _get_shift_swap_request(1234) is None
    assert _get_shift_swap_request(ssr.pk) == ssr


@pytest.mark.django_db
def test_get_user_and_device(make_organization, make_user):
    organization = make_organization()
    user = make_user(organization=organization)

    # no user found
    assert _get_user_and_device(1234) is None

    # no device found
    assert _get_user_and_device(user.pk) is None

    # no mobile app user settings found
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")
    assert _get_user_and_device(user.pk) is None

    # info notifications disabled
    mobile_app_settings = MobileAppUserSettings.objects.create(user=user, info_notifications_enabled=False)
    assert _get_user_and_device(user.pk) is None

    mobile_app_settings.info_notifications_enabled = True
    mobile_app_settings.save()

    assert _get_user_and_device(user.pk) == (user, device, mobile_app_settings)


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
    _mark_shift_swap_request_notified_for_user(shift_swap_request, benefactor, TIMEOUT)
    assert _has_user_been_notified_for_shift_swap_request(shift_swap_request, benefactor) is True

    with patch.object(cache, "set") as mock_cache_set:
        _mark_shift_swap_request_notified_for_user(shift_swap_request, benefactor, TIMEOUT)
        assert mock_cache_set.call_args.kwargs["timeout"] == TIMEOUT


@patch("apps.mobile_app.tasks.new_shift_swap_request._get_user_and_device")
@patch("apps.mobile_app.tasks.new_shift_swap_request.send_push_notification")
@pytest.mark.django_db
def test_notify_beneficiary_about_taken_shift_swap_request(
    mock_send_push_notification,
    mock_get_user_and_device,
    make_organization,
    make_user,
    make_schedule,
    make_shift_swap_request,
):
    organization = make_organization()
    beneficiary = make_user(organization=organization)
    benefactor = make_user(organization=organization)
    schedule_name = "Test Schedule"
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name=schedule_name)

    now = timezone.now()
    swap_start = now + timezone.timedelta(days=100)
    swap_end = swap_start + timezone.timedelta(days=1)

    shift_swap_request = make_shift_swap_request(
        schedule, beneficiary, benefactor=benefactor, swap_start=swap_start, swap_end=swap_end, created_at=now
    )

    device_to_notify = FCMDevice.objects.create(user=beneficiary, registration_id="test_device_id")
    maus = MobileAppUserSettings.objects.create(user=beneficiary, info_notifications_enabled=True)

    # no user, device, or mobile app settings
    mock_get_user_and_device.return_value = None
    notify_beneficiary_about_taken_shift_swap_request(shift_swap_request.pk)
    mock_get_user_and_device.assert_called_once_with(beneficiary.pk)
    mock_send_push_notification.assert_not_called()

    mock_get_user_and_device.reset_mock()

    mock_get_user_and_device.return_value = (beneficiary, device_to_notify, maus)
    notify_beneficiary_about_taken_shift_swap_request(shift_swap_request.pk)
    mock_get_user_and_device.assert_called_once_with(beneficiary.pk)
    mock_send_push_notification.assert_called_once()

    assert mock_send_push_notification.call_args.args[0] == device_to_notify

    message: Message = mock_send_push_notification.call_args.args[1]
    assert message.data["type"] == "oncall.info"
    assert message.data["title"] == add_stack_slug_to_message_title(
        "Your shift swap request has been taken", organization
    )
    assert message.data["subtitle"] == schedule_name
    assert (
        message.data["route"]
        == f"/schedules/{schedule.public_primary_key}/ssrs/{shift_swap_request.public_primary_key}"
    )
    assert message.apns.payload.aps.sound.critical is False
