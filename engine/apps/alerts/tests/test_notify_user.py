from unittest.mock import patch

import pytest
from telegram.error import RetryAfter

from apps.alerts.models import AlertGroup
from apps.alerts.tasks.notify_user import notify_user_task, perform_notification
from apps.api.permissions import LegacyAccessControlRole
from apps.base.models.user_notification_policy import UserNotificationPolicy
from apps.base.models.user_notification_policy_log_record import UserNotificationPolicyLogRecord
from apps.slack.models import SlackMessage
from apps.telegram.models import TelegramToUserConnector

NOTIFICATION_UNAUTHORIZED_MSG = "notification is not allowed for user"


@pytest.mark.django_db
def test_custom_backend_call(
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization = make_organization()
    user_1 = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user_1,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    with patch("apps.base.tests.messaging_backend.TestOnlyBackend.notify_user") as mock_notify_user:
        perform_notification(log_record.pk)

    mock_notify_user.assert_called_once_with(user_1, alert_group, user_notification_policy)


@pytest.mark.django_db
def test_custom_backend_error(
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization = make_organization()
    user_1 = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user_1,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    with patch("apps.alerts.tasks.notify_user.get_messaging_backend_from_id") as mock_get_backend:
        mock_get_backend.return_value = None
        perform_notification(log_record.pk)

    error_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert error_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert error_log_record.reason == "Messaging backend not available"
    assert (
        error_log_record.notification_error_code
        == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "author_set,notification_policy_set",
    [
        (False, True),
        (True, False),
    ],
)
def test_notify_user_missing_data_errors(
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    author_set,
    notification_policy_set,
):
    organization = make_organization()
    user_1 = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user_1 if author_set else None,
        alert_group=alert_group,
        notification_policy=user_notification_policy if notification_policy_set else None,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    with patch("apps.alerts.tasks.notify_user.get_messaging_backend_from_id") as mock_get_backend:
        mock_get_backend.return_value = None
        perform_notification(log_record.pk)

    error_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert error_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert error_log_record.reason == "Expected data is missing"
    assert error_log_record.notification_error_code is None


@pytest.mark.django_db
def test_notify_user_perform_notification_error_if_viewer(
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization = make_organization()
    user_1 = make_user(
        organization=organization, role=LegacyAccessControlRole.VIEWER, _verified_phone_number="1234567890"
    )
    user_notification_policy = make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user_1,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    perform_notification(log_record.pk)

    error_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert error_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert error_log_record.reason == NOTIFICATION_UNAUTHORIZED_MSG
    assert error_log_record.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN


@pytest.mark.django_db
def test_notify_user_error_if_viewer(
    make_organization,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    user_1 = make_user(
        organization=organization, role=LegacyAccessControlRole.VIEWER, _verified_phone_number="1234567890"
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    notify_user_task(user_1.pk, alert_group.pk)

    error_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert error_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert error_log_record.reason == NOTIFICATION_UNAUTHORIZED_MSG
    assert error_log_record.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reason_to_skip_escalation,error_code",
    [
        (AlertGroup.RATE_LIMITED, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_RATELIMIT),
        (AlertGroup.CHANNEL_ARCHIVED, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_CHANNEL_IS_ARCHIVED),
        (AlertGroup.ACCOUNT_INACTIVE, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR),
        (AlertGroup.RESTRICTED_ACTION, UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK),
        (AlertGroup.NO_REASON, None),
    ],
)
def test_perform_notification_reason_to_skip_escalation_in_slack(
    reason_to_skip_escalation,
    error_code,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_slack_message,
):
    organization = make_organization()
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()
    user = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    alert_group.reason_to_skip_escalation = reason_to_skip_escalation
    alert_group.save()
    log_record = make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    if not error_code:
        make_slack_message(alert_group=alert_group, channel_id="test_channel_id", slack_id="test_slack_id")
    with patch.object(SlackMessage, "send_slack_notification") as mocked_send_slack_notification:
        perform_notification(log_record.pk)
    last_log_record = UserNotificationPolicyLogRecord.objects.last()

    if error_code:
        log_reason = f"Skipped escalation in Slack, reason: '{alert_group.get_reason_to_skip_escalation_display()}'"
        mocked_send_slack_notification.assert_not_called()
        assert last_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
        assert last_log_record.reason == log_reason
        assert last_log_record.notification_error_code == error_code
    else:
        mocked_send_slack_notification.assert_called()
        assert last_log_record.type != UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_perform_notification_slack_prevent_posting(
    make_organization,
    make_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_slack_message,
):
    organization = make_organization()
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()
    user = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        slack_prevent_posting=True,
    )
    make_slack_message(alert_group=alert_group, channel_id="test_channel_id", slack_id="test_slack_id")

    with patch.object(SlackMessage, "send_slack_notification") as mocked_send_slack_notification:
        perform_notification(log_record.pk)

    mocked_send_slack_notification.assert_not_called()
    last_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert last_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert last_log_record.reason == "Prevented from posting in Slack"
    assert (
        last_log_record.notification_error_code
        == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED
    )


@pytest.mark.django_db
def test_perform_notification_missing_user_notification_policy_log_record(caplog):
    invalid_pk = 12345
    perform_notification(invalid_pk)

    assert (
        f"perform_notification: log_record {invalid_pk} doesn't exist. Skipping remainder of task. "
        "The alert group associated with this log record may have been deleted."
    ) in caplog.text
    assert f"perform_notification: found record for {invalid_pk}" not in caplog.text


@pytest.mark.django_db
def test_perform_notification_telegram_retryafter_error(
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization, user = make_organization_and_user()
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TELEGRAM,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    countdown = 15
    exc = RetryAfter(countdown)
    with patch.object(TelegramToUserConnector, "notify_user", side_effect=exc) as mock_notify_user:
        with pytest.raises(RetryAfter):
            perform_notification(log_record.pk)

    mock_notify_user.assert_called_once_with(user, alert_group, user_notification_policy)
    assert alert_group.personal_log_records.last() == log_record
