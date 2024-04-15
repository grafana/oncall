from unittest.mock import patch

import pytest

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord


@pytest.mark.django_db
def test_send_slack_notification(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    with patch("apps.slack.client.SlackClient.conversations_members") as mock_members:
        mock_members.return_value = {"members": [slack_user_identity.slack_id]}
        slack_message.send_slack_notification(user, alert_group, notification_policy)

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@pytest.mark.django_db
def test_slack_message_deep_link(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    expected = f"slack://channel?team={slack_team_identity.slack_id}&id={slack_channel.slack_id}&message={slack_message.slack_id}"
    assert slack_message.deep_link == expected
