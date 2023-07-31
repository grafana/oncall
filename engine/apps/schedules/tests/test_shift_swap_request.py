import datetime
from unittest.mock import patch

import pytest

from apps.schedules import exceptions
from apps.schedules.models import ShiftSwapRequest


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
