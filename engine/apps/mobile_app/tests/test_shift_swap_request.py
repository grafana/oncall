import pytest
from django.utils import timezone

from apps.mobile_app.tasks import EARLIEST_NOTIFICATION_OFFSET, WINDOW, _get_shift_swap_requests_to_notify
from apps.schedules.models import OnCallScheduleWeb

MICROSECOND = timezone.timedelta(microseconds=1)


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
