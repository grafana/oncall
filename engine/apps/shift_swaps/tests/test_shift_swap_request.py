import datetime

import pytest
from django.utils import timezone

from apps.schedules.models import OnCallScheduleWeb
from apps.shift_swaps import exceptions
from apps.shift_swaps.models import ShiftSwapRequest


@pytest.fixture
def ssr_setup(make_schedule, make_organization_and_user, make_user_for_organization, make_shift_swap_request):
    def _ssr_setup():
        organization, beneficiary = make_organization_and_user()
        benefactor = make_user_for_organization(organization)

        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        two_days_from_now = tomorrow + datetime.timedelta(days=1)

        ssr = make_shift_swap_request(schedule, beneficiary, swap_start=tomorrow, swap_end=two_days_from_now)

        return ssr, beneficiary, benefactor

    return _ssr_setup


@pytest.mark.django_db
def test_soft_delete(ssr_setup):
    ssr, _, _ = ssr_setup()
    assert ssr.deleted_at is None
    ssr.delete()

    ssr.refresh_from_db()
    assert ssr.deleted_at is not None

    assert ShiftSwapRequest.objects.all().count() == 0
    assert ShiftSwapRequest.objects_with_deleted.all().count() == 1


@pytest.mark.django_db
def test_status_open(ssr_setup) -> None:
    ssr, _, _ = ssr_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN


@pytest.mark.django_db
def test_status_taken(ssr_setup) -> None:
    ssr, _, benefactor = ssr_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN

    ssr.benefactor = benefactor
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.TAKEN


@pytest.mark.django_db
def test_status_past_due(ssr_setup) -> None:
    ssr, _, _ = ssr_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN

    ssr.swap_start = ssr.swap_start - datetime.timedelta(days=5)
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.PAST_DUE


@pytest.mark.django_db
def test_status_deleted(ssr_setup) -> None:
    ssr, _, _ = ssr_setup()
    assert ssr.status == ShiftSwapRequest.Statuses.OPEN

    ssr.delete()
    assert ssr.status == ShiftSwapRequest.Statuses.DELETED


@pytest.mark.django_db
def test_take(ssr_setup) -> None:
    ssr, _, benefactor = ssr_setup()
    original_updated_at = ssr.updated_at

    ssr.take(benefactor)

    assert ssr.benefactor == benefactor
    assert ssr.updated_at != original_updated_at

    # TODO:


@pytest.mark.django_db
def test_take_only_works_for_open_requests(ssr_setup) -> None:
    # already taken
    ssr, _, benefactor = ssr_setup()

    ssr.benefactor = benefactor
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.TAKEN

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)

    # past due
    ssr, _, benefactor = ssr_setup()

    ssr.swap_start = ssr.swap_start - datetime.timedelta(days=5)
    ssr.save()
    assert ssr.status == ShiftSwapRequest.Statuses.PAST_DUE

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)

    # deleted
    ssr, _, benefactor = ssr_setup()

    ssr.delete()
    assert ssr.status == ShiftSwapRequest.Statuses.DELETED

    with pytest.raises(exceptions.ShiftSwapRequestNotOpenForTaking):
        ssr.take(benefactor)


@pytest.mark.django_db
def test_take_own_ssr(ssr_setup) -> None:
    ssr, beneficiary, _ = ssr_setup()
    with pytest.raises(exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest):
        ssr.take(beneficiary)
