from unittest.mock import patch

import pytest

from apps.alerts.models import EscalationPolicy
from apps.alerts.tasks.notify_all import notify_all_task
from apps.base.models.user_notification_policy import UserNotificationPolicy


@pytest.mark.django_db
def test_notify_all(
    make_organization,
    make_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    user = make_user(organization=organization)
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
    # note this is the only escalation step, with order=1
    notify_all = make_escalation_policy(
        order=1,
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_FINAL_NOTIFYALL,
    )
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel, channel_filter=channel_filter)
    # build escalation snapshot
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    with patch(
        "apps.slack.models.SlackTeamIdentity.get_users_from_slack_conversation_for_organization"
    ) as mock_get_users:
        mock_get_users.return_value = [user]
        with patch("apps.alerts.tasks.notify_all.notify_user_task") as mock_notify_user_task:
            notify_all_task(alert_group.pk, escalation_policy_snapshot_order=1)

    alert_group.refresh_from_db()

    # check triggered log
    log_record = alert_group.log_records.last()
    assert log_record.type == log_record.TYPE_ESCALATION_TRIGGERED
    assert log_record.author == user
    assert log_record.escalation_policy == notify_all
    assert log_record.escalation_policy_step == EscalationPolicy.STEP_FINAL_NOTIFYALL

    # check user is notified
    mock_notify_user_task.apply_async.assert_called_once_with(
        args=(user.pk, alert_group.pk),
        kwargs={"reason": "notifying everyone in the channel", "prevent_posting_to_thread": True},
        countdown=0,
    )

    escalation_snapshot = alert_group.escalation_snapshot
    assert escalation_snapshot is not None
    assert escalation_snapshot.escalation_policies_snapshots[0].notify_to_users_queue == [user]
