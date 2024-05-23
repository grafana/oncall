from unittest.mock import patch

import pytest

from apps.alerts.models import EscalationPolicy
from apps.alerts.tasks.notify_group import notify_group_task
from apps.base.models.user_notification_policy import UserNotificationPolicy


@pytest.mark.django_db
def test_notify_group(
    make_organization,
    make_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_slack_user_group,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    user = make_user(organization=organization)
    # remove default email escalation policies
    user.notification_policies.all().delete()
    make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)

    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        escalation_chain=escalation_chain,
        notify_in_slack=True,
        slack_channel_id="slack-channel-id",
    )
    usergroup = make_slack_user_group(slack_team_identity)
    # note this is the only escalation step, with order=1
    notify_group = make_escalation_policy(
        order=1,
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_GROUP,
        notify_to_group=usergroup,
    )
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel, channel_filter=channel_filter)
    # build escalation snapshot
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    with patch("apps.slack.models.SlackUserGroup.get_users_from_members_for_organization") as mock_get_users:
        mock_get_users.return_value = [user]
        with patch("apps.alerts.tasks.notify_group.notify_user_task") as mock_notify_user_task:
            notify_group_task(alert_group.pk, escalation_policy_snapshot_order=1)

    alert_group.refresh_from_db()

    # check triggered log
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.escalation_policy == notify_group
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_NOTIFY_GROUP
    assert log_record.step_specific_info == {"usergroup_handle": usergroup.handle}

    # check user is notified
    mock_notify_user_task.apply_async.assert_called_once_with(
        args=(user.pk, alert_group.pk),
        kwargs={
            "reason": f"Membership in <!subteam^{usergroup.slack_id}> User Group",
            "prevent_posting_to_thread": True,
            "important": False,
        },
    )

    escalation_snapshot = alert_group.escalation_snapshot
    assert escalation_snapshot is not None
    assert escalation_snapshot.escalation_policies_snapshots[0].notify_to_users_queue == [user]
