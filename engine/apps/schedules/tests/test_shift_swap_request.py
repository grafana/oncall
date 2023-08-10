import datetime
from unittest.mock import patch

import pytest
import pytz
from django.utils import timezone

from apps.schedules import exceptions
from apps.schedules.models import CustomOnCallShift, ShiftSwapRequest
from apps.user_management.models import User

ROTATION_START = datetime.datetime(2150, 8, 29, 0, 0, 0, 0, tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_soft_delete(shift_swap_request_setup):
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.deleted_at is None

    with patch("apps.schedules.models.shift_swap_request.refresh_ical_final_schedule") as mock_refresh_final:
        ssr.delete()

    ssr.refresh_from_db()
    assert ssr.deleted_at is not None

    assert mock_refresh_final.apply_async.called_with((ssr.schedule.pk,))

    assert ShiftSwapRequest.objects.all().count() == 0
    assert ShiftSwapRequest.objects_with_deleted.all().count() == 1


@pytest.mark.django_db
def test_status_open(shift_swap_request_setup) -> None:
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN


@pytest.mark.django_db
def test_status_taken(shift_swap_request_setup) -> None:
    ssr, _, benefactor = shift_swap_request_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN
    assert ssr.is_taken is False

    ssr.benefactor = benefactor
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.TAKEN
    assert ssr.is_taken is True

    # taken in the past it's still taken
    now = timezone.now()
    ssr.swap_start = now - timezone.timedelta(days=2)
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.TAKEN
    assert ssr.is_taken is True
    assert ssr.is_past_due is False


@pytest.mark.django_db
def test_status_past_due(shift_swap_request_setup) -> None:
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN
    assert ssr.is_past_due is False

    ssr.swap_start = ssr.swap_start - datetime.timedelta(days=5)
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.PAST_DUE
    assert ssr.is_past_due is True


@pytest.mark.django_db
def test_status_deleted(shift_swap_request_setup) -> None:
    ssr, _, _ = shift_swap_request_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN
    assert ssr.is_deleted is False

    ssr.delete()
    assert ssr.status == ShiftSwapRequest.Statuses.DELETED
    assert ssr.is_deleted is True


@pytest.mark.django_db
def test_take(shift_swap_request_setup) -> None:
    ssr, _, benefactor = shift_swap_request_setup()
    original_updated_at = ssr.updated_at

    with patch("apps.schedules.models.shift_swap_request.refresh_ical_final_schedule") as mock_refresh_final:
        ssr.take(benefactor)

    assert ssr.benefactor == benefactor
    assert ssr.updated_at != original_updated_at
    # final schedule refresh was triggered
    assert mock_refresh_final.apply_async.called_with((ssr.schedule.pk,))


@pytest.mark.django_db
def test_take_only_works_for_open_requests(shift_swap_request_setup) -> None:
    # already taken
    ssr, _, benefactor = shift_swap_request_setup()

    ssr.benefactor = benefactor
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.TAKEN

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)

    # past due
    ssr, _, benefactor = shift_swap_request_setup()

    ssr.swap_start = ssr.swap_start - datetime.timedelta(days=5)
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.PAST_DUE

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)

    # deleted
    ssr, _, benefactor = shift_swap_request_setup()

    ssr.delete()
    assert ssr.status == ShiftSwapRequest.Statuses.DELETED

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)


@pytest.mark.django_db
def test_take_own_ssr(shift_swap_request_setup) -> None:
    ssr, beneficiary, _ = shift_swap_request_setup()
    with pytest.raises(exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest):
        ssr.take(beneficiary)


@pytest.mark.skip(
    "Skipping as flaky based on time of day that the test runs. Example failure here https://github.com/grafana/oncall/actions/runs/5747168275/job/15577755519?pr=2725#step:5:1005"
)
@pytest.mark.django_db
def test_related_shifts(shift_swap_request_setup, make_on_call_shift) -> None:
    ssr, beneficiary, _ = shift_swap_request_setup()

    schedule = ssr.schedule
    organization = schedule.organization
    user = beneficiary

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(days=2)
    duration = timezone.timedelta(hours=8)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    events = ssr.shifts()

    expected = [
        # start, end, user, swap request ID
        (start, start + duration, user.public_primary_key, ssr.public_primary_key),
    ]
    returned_events = [(e["start"], e["end"], e["users"][0]["pk"], e["users"][0]["swap_request"]["pk"]) for e in events]
    assert returned_events == expected


@pytest.mark.django_db
def test_possible_benefactors(shift_swap_request_setup) -> None:
    ssr, beneficiary, benefactor = shift_swap_request_setup()

    with patch.object(ssr.schedule, "related_users") as mock_related_users:
        mock_related_users.return_value = User.objects.filter(pk__in=[beneficiary.pk, benefactor.pk])
        assert list(ssr.possible_benefactors) == [benefactor]
