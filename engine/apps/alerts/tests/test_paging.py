from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertGroupLogRecord, UserHasNotification
from apps.alerts.paging import (
    DirectPagingUserTeamValidationError,
    _construct_title,
    direct_paging,
    unpage_user,
    user_is_oncall,
)
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb


def assert_log_record(alert_group, reason, log_type=AlertGroupLogRecord.TYPE_DIRECT_PAGING, expected_info=None):
    log = alert_group.log_records.filter(alert_group=alert_group, type=log_type, reason=reason).first()
    assert log is not None
    if expected_info is not None:
        assert log.get_step_specific_info() == expected_info


@pytest.mark.django_db
def test_user_is_oncall(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    not_oncall_user = make_user_for_organization(organization)
    oncall_user = make_user_for_organization(organization)

    # set up schedule: user is on call
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        team=None,
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(hours=23, minutes=59, seconds=59),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[oncall_user]])
    schedule.refresh_ical_file()

    assert user_is_oncall(not_oncall_user) is False
    assert user_is_oncall(oncall_user) is True


@pytest.mark.django_db
def test_direct_paging_user(make_organization, make_user_for_organization, django_capture_on_commit_callbacks):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    msg = "Fire"

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with patch("apps.alerts.paging.notify_user_task") as notify_task:
            direct_paging(organization, from_user, msg, users=[(user, False), (other_user, True)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()

    assert alert.title == f"{from_user.username} is paging {user.username} and {other_user.username} to join escalation"
    assert alert.message == msg

    # callbacks: distribute_alert + 2 notify_user tasks
    assert len(callbacks) == 3
    # notifications sent
    for u, important in ((user, False), (other_user, True)):
        notify_task.apply_async.assert_any_call(
            (u.pk, ag.pk), {"important": important, "notify_even_acknowledged": True, "notify_anyway": True}
        )
        expected_info = {"user": u.public_primary_key, "important": important}
        assert_log_record(ag, f"{from_user.username} paged user {u.username}", expected_info=expected_info)


@pytest.mark.django_db
def test_direct_paging_team(make_organization, make_team, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    team = make_team(organization)
    msg = "Fire"

    direct_paging(organization, from_user, msg, team=team)

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()
    assert alert.title == f"{from_user.username} is paging {team.name} to join escalation"
    assert alert.message == msg

    assert ag.channel.verbal_name == f"Direct paging ({team.name} team)"
    assert ag.channel.team == team


@pytest.mark.django_db
def test_direct_paging_no_team(make_organization, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    msg = "Fire"

    direct_paging(organization, from_user, msg, users=[(other_user, False)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()
    assert alert.title == f"{from_user.username} is paging {other_user.username} to join escalation"
    assert alert.message == msg

    assert ag.channel.verbal_name == "Direct paging (No team)"
    assert ag.channel.team is None


@pytest.mark.django_db
def test_direct_paging_custom_title(make_organization, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    custom_title = "Custom title"
    msg = "Fire"

    direct_paging(organization, from_user, msg, custom_title, users=[(other_user, False)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()

    assert ag.web_title_cache == custom_title
    assert ag.alerts.get().title == custom_title


@pytest.mark.django_db
def test_direct_paging_no_team_and_no_users(make_organization, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    msg = "Fire"

    with pytest.raises(DirectPagingUserTeamValidationError):
        direct_paging(organization, from_user, msg)


@pytest.mark.django_db
def test_direct_paging_reusing_alert_group(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    django_capture_on_commit_callbacks,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    with django_capture_on_commit_callbacks(execute=True):
        with patch("apps.alerts.paging.notify_user_task") as notify_task:
            direct_paging(organization, from_user, "Fire!", users=[(user, False)], alert_group=alert_group)

    # no new alert group is created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    assert_log_record(alert_group, f"{from_user.username} paged user {user.username}")

    # notifications sent
    ag = alert_groups.get()
    notify_task.apply_async.assert_has_calls(
        [call((user.pk, ag.pk), {"important": False, "notify_even_acknowledged": True, "notify_anyway": True})]
    )


@pytest.mark.django_db
def test_direct_paging_returns_alert_group(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)

    with patch("apps.alerts.paging.notify_user_task"):
        alert_group = direct_paging(organization, from_user, "Help!", users=[(user, False)])

    # check alert group returned by direct paging is the same as the one created
    assert alert_group == AlertGroup.objects.get()


@pytest.mark.django_db
def test_unpage_user_not_exists(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    unpage_user(alert_group, user, from_user)


@pytest.mark.django_db
def test_unpage_user_ok(make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    # setup user has notification entry
    user_has_notification = UserHasNotification.objects.create(
        alert_group=alert_group, user=user, active_notification_policy_id="task-id"
    )

    unpage_user(alert_group, user, from_user)

    user_has_notification.refresh_from_db()
    assert user_has_notification.active_notification_policy_id is None
    assert_log_record(
        alert_group, f"{from_user.username} unpaged user {user.username}", AlertGroupLogRecord.TYPE_UNPAGE_USER
    )


@pytest.mark.django_db
def test_direct_paging_always_create_group(
    make_organization,
    make_user_for_organization,
    django_capture_on_commit_callbacks,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    msg = "Help!"
    users = [(user, False)]

    with django_capture_on_commit_callbacks(execute=True):
        with patch("apps.alerts.paging.notify_user_task") as notify_task:
            # although calling twice with same params, there should be 2 alert groups
            direct_paging(organization, from_user, msg, users=users)
            direct_paging(organization, from_user, msg, users=users)

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 2

    # notifications sent
    notify_task.apply_async.assert_has_calls(
        [
            call(
                (user.pk, alert_groups[0].pk),
                {"important": False, "notify_even_acknowledged": True, "notify_anyway": True},
            ),
            call(
                (user.pk, alert_groups[1].pk),
                {"important": False, "notify_even_acknowledged": True, "notify_anyway": True},
            ),
        ],
        any_order=True,
    )


@pytest.mark.django_db
def test_construct_title(make_organization, make_team, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    user1 = make_user_for_organization(organization)
    user2 = make_user_for_organization(organization)
    user3 = make_user_for_organization(organization)
    team = make_team(organization)

    def _title(middle_portion: str) -> str:
        return f"{from_user.username} is paging {middle_portion} to join escalation"

    one_user = [(user1, False)]
    two_users = [(user1, False), (user2, True)]
    multiple_users = two_users + [(user3, False)]

    # no team specified + one user
    assert _construct_title(from_user, None, one_user) == _title(user1.username)

    # no team specified + two users
    assert _construct_title(from_user, None, two_users) == _title(f"{user1.username} and {user2.username}")

    # no team specified + multiple users
    assert _construct_title(from_user, None, multiple_users) == _title(
        f"{user1.username}, {user2.username} and {user3.username}"
    )

    # team specified + no users
    assert _construct_title(from_user, team, []) == _title(team.name)

    # team specified + one user
    assert _construct_title(from_user, team, one_user) == _title(f"{team.name} and {user1.username}")

    # team specified + two users
    assert _construct_title(from_user, team, two_users) == _title(f"{team.name}, {user1.username} and {user2.username}")

    # team specified + multiple users
    assert _construct_title(from_user, team, multiple_users) == _title(
        f"{team.name}, {user1.username}, {user2.username} and {user3.username}"
    )
