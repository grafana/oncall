import pytest
from django.utils import timezone

from apps.schedules.ical_utils import list_users_to_notify_from_ical, users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar
from common.constants.role import Role


@pytest.mark.django_db
@pytest.mark.parametrize(
    "include_viewers",
    [True, False],
)
def test_users_in_ical_viewers_inclusion(make_organization_and_user, make_user_for_organization, include_viewers):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, Role.VIEWER)

    usernames = [user.username, viewer.username]
    result = users_in_ical(usernames, organization, include_viewers=include_viewers)
    if include_viewers:
        assert set(result) == {user, viewer}
    else:
        assert set(result) == {user}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "include_viewers",
    [True, False],
)
def test_list_users_to_notify_from_ical_viewers_inclusion(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift, include_viewers
):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, Role.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    date = timezone.now().replace(tzinfo=None, microsecond=0)
    data = {
        "priority_level": 1,
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)
    on_call_shift.users.add(viewer)
    schedule.custom_on_call_shifts.add(on_call_shift)

    # get users on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date, include_viewers=include_viewers)

    if include_viewers:
        assert len(users_on_call) == 2
        assert set(users_on_call) == {user, viewer}
    else:
        assert len(users_on_call) == 1
        assert set(users_on_call) == {user}
