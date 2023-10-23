from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroup, AlertGroupLogRecord, UserHasNotification
from apps.alerts.paging import DirectPagingUserTeamValidationError, direct_paging, unpage_user


def _calculate_title(from_user) -> str:
    return f"Direct page from {from_user.username}"


def assert_log_record(alert_group, reason, log_type=AlertGroupLogRecord.TYPE_DIRECT_PAGING, expected_info=None):
    log = alert_group.log_records.filter(alert_group=alert_group, type=log_type, reason=reason).first()
    assert log is not None
    if expected_info is not None:
        assert log.get_step_specific_info() == expected_info


@pytest.mark.django_db
def test_direct_paging_user(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    msg = "Fire"

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        direct_paging(organization, from_user, msg, users=[(user, False), (other_user, True)])

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()

    assert alert.title == _calculate_title(from_user)
    assert alert.message == msg

    # notifications sent
    for u, important in ((user, False), (other_user, True)):
        assert notify_task.apply_async.called_with(
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

    direct_paging(organization, from_user, msg, team)

    # alert group created
    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()
    assert alert.title == _calculate_title(from_user)
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
    assert alert.title == _calculate_title(from_user)
    assert alert.message == msg

    assert ag.channel.verbal_name == "Direct paging (No team)"
    assert ag.channel.team is None


@pytest.mark.django_db
def test_direct_paging_no_team_and_no_users(make_organization, make_user_for_organization):
    organization = make_organization()
    from_user = make_user_for_organization(organization)
    msg = "Fire"

    with pytest.raises(DirectPagingUserTeamValidationError):
        direct_paging(organization, from_user, msg)


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
        direct_paging(organization, from_user, "Fire!", users=[(user, False)], alert_group=alert_group)

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
def test_direct_paging_always_create_group(make_organization, make_user_for_organization):
    organization = make_organization()
    user = make_user_for_organization(organization)
    from_user = make_user_for_organization(organization)
    msg = "Help!"
    users = [(user, False)]

    with patch("apps.alerts.paging.notify_user_task") as notify_task:
        # although calling twice with same params, there should be 2 alert groups
        direct_paging(organization, from_user, msg, users=users)
        direct_paging(organization, from_user, msg, users=users)

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
