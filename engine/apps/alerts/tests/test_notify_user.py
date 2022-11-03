from unittest.mock import patch

import pytest

from apps.alerts.tasks.notify_user import notify_user_task, perform_notification
from apps.api.permissions import LegacyAccessControlRole
from apps.base.models.user_notification_policy import UserNotificationPolicy
from apps.base.models.user_notification_policy_log_record import UserNotificationPolicyLogRecord

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
