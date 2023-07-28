from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertGroupLogRecord, UserHasNotification
from apps.alerts.paging import PagingError, check_user_availability, direct_paging, unpage_user
from apps.base.models import UserNotificationPolicy
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb


def assert_log_record(alert_group, reason, log_type=AlertGroupLogRecord.TYPE_DIRECT_PAGING, expected_info=None):
    log = alert_group.log_records.filter(alert_group=alert_group, type=log_type, reason=reason).first()
    assert log is not None
    if expected_info is not None:
        assert log.get_step_specific_info() == expected_info


def setup_always_on_call_schedule(make_schedule, make_on_call_shift, organization, team, user, extra_users=None):
    # setup on call schedule
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        team=team,
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
    on_call_shift.add_rolling_users([[user]])
    if extra_users:
        # add old shifts for users
        for i, u in enumerate(extra_users):
            start_date = now - timezone.timedelta(days=14)
            data = {
                "start": start_date + timezone.timedelta(hours=i),
                "rotation_start": start_date,
                "duration": timezone.timedelta(hours=1),
                "priority_level": 1,
                "frequency": CustomOnCallShift.FREQUENCY_DAILY,
                "schedule": schedule,
                "until": start_date + timezone.timedelta(days=7),
            }
            on_call_shift = make_on_call_shift(
                organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
            )
            on_call_shift.add_rolling_users([[u]])

    schedule.refresh_ical_file()
    return schedule


@pytest.mark.django_db
def test_check_user_availability_no_policies(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)

    warnings = check_user_availability(user)
    assert warnings == [
        {"data": {}, "error": PagingError.USER_HAS_NO_NOTIFICATION_POLICY},
        {"data": {"schedules": {}}, "error": PagingError.USER_IS_NOT_ON_CALL},
    ]


@pytest.mark.django_db
def test_check_user_availability_not_on_call(
    make_organization, make_user_for_organization, make_user_notification_policy, make_schedule, make_on_call_shift
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )

    # setup on call schedule
    schedule = setup_always_on_call_schedule(
        make_schedule, make_on_call_shift, organization, None, other_user, extra_users=[user]
    )

    warnings = check_user_availability(user)
    assert warnings == [
        {
            "data": {"schedules": {schedule.name: {other_user.public_primary_key}}},
            "error": PagingError.USER_IS_NOT_ON_CALL,
        },
    ]


@pytest.mark.django_db
def test_check_user_availability_on_call(
    make_organization,
    make_team,
    make_user_for_organization,
    make_user_notification_policy,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    some_team = make_team(organization)
    user = make_user_for_organization(organization)
    make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )

    # setup on call schedule
    setup_always_on_call_schedule(make_schedule, make_on_call_shift, organization, some_team, user)

    warnings = check_user_availability(user)
    assert warnings == []


@pytest.mark.django_db
def test_direct_paging_user(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        direct_paging(
            organization, None, from_user, title="Help!", message="Fire", users=[(user, False), (other_user, True)]
        )

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()
    assert alert.title == "Help!"
    assert alert.message == "Fire"
    # notifications sent
    for u, important in ((user, False), (other_user, True)):
        assert notify_task.apply_async.called_with(
            (u.pk, ag.pk), {"important": important, "notify_even_acknowledged": True, "notify_anyway": True}
        )
        expected_info = {"user": u.public_primary_key, "schedule": None, "important": important}
        assert_log_record(ag, f"{from_user.username} paged user {u.username}", expected_info=expected_info)


@pytest.mark.django_db
def test_direct_paging_schedule(
    make_organization, make_team, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization = make_organization()
    some_team = make_team(organization)
    from_user = make_user_for_organization(organization)
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    # setup on call schedule
    schedule = setup_always_on_call_schedule(make_schedule, make_on_call_shift, organization, some_team, user)
    other_schedule = setup_always_on_call_schedule(
        make_schedule, make_on_call_shift, organization, some_team, other_user
    )

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        direct_paging(organization, None, from_user, schedules=[(schedule, False), (other_schedule, True)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()
    assert alert.title == f"Message from {from_user.username}"
    assert alert.message is None
    assert_log_record(ag, f"{from_user.username} paged schedule {schedule.name}")
    assert_log_record(ag, f"{from_user.username} paged schedule {other_schedule.name}")
    # notifications sent
    for u, important, s in ((user, False, schedule), (other_user, True, other_schedule)):
        assert notify_task.apply_async.called_with(
            (u.pk, ag.pk), {"important": important, "notify_even_acknowledged": True, "notify_anyway": True}
        )
        expected_info = {"user": u.public_primary_key, "schedule": s.public_primary_key, "important": important}
        assert_log_record(
            ag, f"{from_user.username} paged user {u.username} (from schedule {s.name})", expected_info=expected_info
        )


@pytest.mark.django_db
def test_direct_paging_reusing_alert_group(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        direct_paging(organization, None, from_user, users=[(user, False)], alert_group=alert_group)

    # no new alert group is created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    assert_log_record(alert_group, f"{from_user.username} paged user {user.username}")
    # notifications sent
    ag = alert_groups.get()
    assert notify_task.apply_async.called_with(
        (user.pk, ag.pk), {"important": False, "notify_even_acknowledged": True, "notify_anyway": True}
    )


@pytest.mark.django_db
def test_direct_paging_reusing_alert_group_custom_chain_raises(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group, make_escalation_chain
):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    custom_chain = make_escalation_chain(organization)

    with pytest.raises(ValueError):
        direct_paging(organization, None, from_user, alert_group=alert_group, escalation_chain=custom_chain)


@pytest.mark.django_db
def test_direct_paging_custom_chain(
    make_organization, make_user_for_organization, make_alert_receive_channel, make_alert_group, make_escalation_chain
):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    custom_chain = make_escalation_chain(organization)

    direct_paging(organization, None, from_user, escalation_chain=custom_chain)

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    channel_filter = ag.channel_filter_with_respect_to_escalation_snapshot
    assert channel_filter is not None
    assert not channel_filter.is_default
    assert channel_filter.notify_in_slack
    assert ag.escalation_chain_with_respect_to_escalation_snapshot == custom_chain


@pytest.mark.django_db
def test_direct_paging_returns_alert_group(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)

    with patch("apps.alerts.paging.notify_user_task"):
        alert_group = direct_paging(organization, None, from_user, title="Help!", message="Fire", users=[(user, False)])

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
def test_direct_paging_always_create_group(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        # although calling twice with same params, there should be 2 alert groups
        direct_paging(organization, None, from_user, title="Help!", users=[(user, False)])
        direct_paging(organization, None, from_user, title="Help!", users=[(user, False)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 2
    # notifications sent
    assert notify_task.apply_async.called_with(
        (user.pk, alert_groups[0].pk), {"important": False, "notify_even_acknowledged": True, "notify_anyway": True}
    )
    assert notify_task.apply_async.called_with(
        (user.pk, alert_groups[1].pk), {"important": False, "notify_even_acknowledged": True, "notify_anyway": True}
    )
