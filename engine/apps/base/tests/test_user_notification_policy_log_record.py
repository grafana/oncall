import pytest

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.base.tests.messaging_backend import TestOnlyBackend


@pytest.mark.django_db
def test_extra_messaging_backends_error_log(
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
        notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
    )

    output = log_record.render_log_line_action()
    assert output == f"failed to notify {user_1.username} by {TestOnlyBackend.label.lower()}"


@pytest.mark.django_db
def test_extra_messaging_backends_sent_log(
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

    output = log_record.render_log_line_action()
    assert output == f"sent {TestOnlyBackend.label.lower()} message to {user_1.username}"
