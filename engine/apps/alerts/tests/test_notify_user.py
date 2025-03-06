from unittest.mock import patch

import pytest
from django.utils import timezone
from telegram.error import RetryAfter

from apps.alerts.models import AlertGroup
from apps.alerts.paging import direct_paging
from apps.alerts.tasks.notify_user import notify_user_task, perform_notification, send_bundled_notification
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
        perform_notification(log_record.pk, False)

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
        perform_notification(log_record.pk, False)

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
        perform_notification(log_record.pk, False)

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

    perform_notification(log_record.pk, False)

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
def test_notify_user_perform_notification_skip_if_resolved(
    make_organization,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization = make_organization()
    user_1 = make_user(organization=organization, _verified_phone_number="1234567890")
    user_notification_policy = make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel, resolved=True)
    log_record = make_user_notification_policy_log_record(
        author=user_1,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    perform_notification(log_record.pk, False)

    error_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert error_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert error_log_record.reason == "Skipped notification because alert group is resolved"


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
    make_organization_with_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_slack_channel,
    make_slack_message,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    user = make_user(organization=organization)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)

    alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        reason_to_skip_escalation=reason_to_skip_escalation,
    )

    log_record = make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    if not error_code:
        slack_channel = make_slack_channel(slack_team_identity=slack_team_identity)
        make_slack_message(slack_channel, alert_group=alert_group)

    with patch.object(SlackMessage, "send_slack_notification") as mocked_send_slack_notification:
        perform_notification(log_record.pk, False)

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
    make_organization_with_slack_team_identity,
    make_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_slack_channel,
    make_slack_message,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

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

    slack_channel = make_slack_channel(slack_team_identity=slack_team_identity)
    make_slack_message(slack_channel, alert_group=alert_group)

    with patch.object(SlackMessage, "send_slack_notification") as mocked_send_slack_notification:
        perform_notification(log_record.pk, False)

    mocked_send_slack_notification.assert_not_called()
    last_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert last_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS
    assert last_log_record.reason == "Prevented from posting in Slack"
    assert (
        last_log_record.notification_error_code
        == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED
    )


@pytest.mark.django_db
def test_perform_notification_missing_user_notification_policy_log_record(caplog):
    invalid_pk = 12345
    perform_notification(invalid_pk, False)

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
        with patch.object(perform_notification, "apply_async") as mock_apply_async:
            perform_notification(log_record.pk, False)

    mock_notify_user.assert_called_once_with(user, alert_group, user_notification_policy)
    # task is rescheduled using the countdown value from the exception
    mock_apply_async.assert_called_once_with((log_record.pk, False), countdown=countdown)
    assert alert_group.personal_log_records.last() == log_record

    # but if the log was too old, skip and create a failed log record
    log_record.created_at = timezone.now() - timezone.timedelta(minutes=90)
    log_record.save()
    with patch.object(TelegramToUserConnector, "notify_user", side_effect=exc) as mock_notify_user:
        with patch.object(perform_notification, "apply_async") as mock_apply_async:
            perform_notification(log_record.pk, False)
    mock_notify_user.assert_called_once_with(user, alert_group, user_notification_policy)
    assert not mock_apply_async.called
    last_log_record = UserNotificationPolicyLogRecord.objects.last()
    assert last_log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert last_log_record.reason == "Telegram rate limit exceeded"
    assert (
        last_log_record.notification_error_code
        == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_TELEGRAM_RATELIMIT
    )


@patch("apps.base.models.UserNotificationPolicy.get_default_fallback_policy")
@patch("apps.base.tests.messaging_backend.TestOnlyBackend.notify_user")
@pytest.mark.django_db
def test_perform_notification_use_default_notification_policy_fallback(
    mock_notify_user,
    mock_get_default_fallback_policy,
    make_organization,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    organization = make_organization()
    user = make_user(organization=organization)
    fallback_notification_policy = UserNotificationPolicy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
        important=False,
        order=0,
    )

    mock_get_default_fallback_policy.return_value = fallback_notification_policy

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    log_record = make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=None,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )

    perform_notification(log_record.pk, True)

    mock_notify_user.assert_called_once_with(user, alert_group, fallback_notification_policy)


@pytest.mark.django_db
def test_notify_user_task_notification_bundle_is_enabled(
    make_organization_and_user,
    make_user_for_organization,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    settings,
):
    settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED = True
    organization, user_1 = make_organization_and_user()
    user_2 = make_user_for_organization(organization)
    make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,  # channel is in NOTIFICATION_CHANNELS_TO_BUNDLE
    )
    make_user_notification_policy(
        user=user_1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
        important=True,
    )
    make_user_notification_policy(
        user=user_2,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,  # channel is not in NOTIFICATION_CHANNELS_TO_BUNDLE
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group_1 = make_alert_group(alert_receive_channel=alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel=alert_receive_channel)
    assert not user_1.notification_bundles.exists()
    # send 1st notification to user_1, check notification_bundle was created
    # without scheduling send_bundled_notification task
    notify_user_task(user_1.id, alert_group_1.id)
    assert user_1.notification_bundles.count() == 1
    notification_bundle = user_1.notification_bundles.first()
    assert notification_bundle.notification_task_id is None
    assert not notification_bundle.notifications.exists()
    # send 2nd notification to user_1, check bundled notification was attached to notification_bundle
    # and send_bundled_notification was scheduled
    notify_user_task(user_1.id, alert_group_2.id)
    notification_bundle.refresh_from_db()
    assert notification_bundle.notifications.count() == 1
    assert notification_bundle.notification_task_id is not None
    # send important notification to user_1, check new notification_bundle was created
    notify_user_task(user_1.id, alert_group_1.id, important=True)
    assert user_1.notification_bundles.count() == 2
    important_notification_bundle = user_1.notification_bundles.get(important=True)
    assert important_notification_bundle.notification_task_id is None
    assert not important_notification_bundle.notifications.exists()
    # send notification to user_2 (notification channel is not in NOTIFICATION_CHANNELS_TO_BUNDLE),
    # check notification_bundle was not created
    notify_user_task(user_2.id, alert_group_1.id)
    assert not user_2.notification_bundles.exists()


@pytest.mark.django_db
def test_notify_user_task_notification_bundle_is_not_enabled(
    make_organization_and_user,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    settings,
):
    settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED = False
    organization, user = make_organization_and_user()
    make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,  # channel is in NOTIFICATION_CHANNELS_TO_BUNDLE
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    # send notification, check notification_bundle was not created
    notify_user_task(user.id, alert_group.id)
    assert not user.notification_bundles.exists()


@pytest.mark.django_db
def test_send_bundle_notification(
    make_organization_and_user,
    make_user_notification_policy,
    make_user_notification_bundle,
    make_alert_receive_channel,
    make_alert_group,
    settings,
    caplog,
):
    settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED = True
    organization, user = make_organization_and_user()
    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,  # channel is in NOTIFICATION_CHANNELS_TO_BUNDLE
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group_1 = make_alert_group(alert_receive_channel=alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel=alert_receive_channel)
    alert_group_3 = make_alert_group(alert_receive_channel=alert_receive_channel)

    task_id = "test_task_id"
    notification_bundle = make_user_notification_bundle(
        user, UserNotificationPolicy.NotificationChannel.SMS, notification_task_id=task_id, eta=timezone.now()
    )

    notification_bundle.append_notification(alert_group_1, notification_policy)
    notification_bundle.append_notification(alert_group_2, notification_policy)
    notification_bundle.append_notification(alert_group_3, notification_policy)

    assert notification_bundle.notifications.filter(bundle_uuid__isnull=True).count() == 3

    alert_group_3.resolve()

    # send notification for 2 active alert groups
    send_bundled_notification.apply((notification_bundle.id,), task_id=task_id)

    assert f"alert_group {alert_group_3.id} is not active, skip notification" in caplog.text
    assert "perform bundled notification for alert groups with ids:" in caplog.text

    # check bundle_uuid was set, notification for resolved alert group was deleted
    assert notification_bundle.notifications.filter(bundle_uuid__isnull=True).count() == 0
    assert notification_bundle.notifications.all().count() == 2
    assert not notification_bundle.notifications.filter(alert_group=alert_group_3).exists()

    # send notification for 1 active alert group
    notification_bundle.notifications.update(bundle_uuid=None)

    # since we're calling send_bundled_notification several times within this test, we need to reset task_id
    # because it gets set to None after the first call
    notification_bundle.notification_task_id = task_id
    notification_bundle.save()

    alert_group_2.resolve()

    send_bundled_notification.apply((notification_bundle.id,), task_id=task_id)

    assert f"alert_group {alert_group_2.id} is not active, skip notification" in caplog.text
    assert (
        f"there is only one alert group in bundled notification, perform regular notification. "
        f"alert_group {alert_group_1.id}"
    ) in caplog.text

    # check bundle_uuid was set
    assert notification_bundle.notifications.filter(bundle_uuid__isnull=True).count() == 0
    assert notification_bundle.notifications.all().count() == 1

    # cleanup notifications
    notification_bundle.notifications.all().delete()

    # send notification for 0 active alert group
    notification_bundle.append_notification(alert_group_1, notification_policy)

    # since we're calling send_bundled_notification several times within this test, we need to reset task_id
    # because it gets set to None after the first call
    notification_bundle.notification_task_id = task_id
    notification_bundle.save()

    alert_group_1.resolve()

    send_bundled_notification.apply((notification_bundle.id,), task_id=task_id)

    assert f"alert_group {alert_group_1.id} is not active, skip notification" in caplog.text
    assert f"no alert groups to notify about or notification is not allowed for user {user.id}" in caplog.text

    # check all notifications were deleted
    assert notification_bundle.notifications.all().count() == 0


@pytest.mark.django_db
def test_send_bundle_notification_task_id_mismatch(
    make_organization_and_user,
    make_user_notification_bundle,
    settings,
    caplog,
):
    settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED = True
    organization, user = make_organization_and_user()
    notification_bundle = make_user_notification_bundle(
        user, UserNotificationPolicy.NotificationChannel.SMS, notification_task_id="test_task_id", eta=timezone.now()
    )
    send_bundled_notification(notification_bundle.id)
    assert (
        f"send_bundled_notification: notification_task_id mismatch. "
        f"Duplication or non-active notification triggered. "
        f"Active: {notification_bundle.notification_task_id}"
    ) in caplog.text


@pytest.mark.django_db
def test_notify_user_task_notification_bundle_eta_is_outdated(
    make_organization_and_user,
    make_user_for_organization,
    make_user_notification_policy,
    make_user_notification_bundle,
    make_alert_receive_channel,
    make_alert_group,
    settings,
):
    settings.FEATURE_NOTIFICATION_BUNDLE_ENABLED = True
    organization, user = make_organization_and_user()
    notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,  # channel is in NOTIFICATION_CHANNELS_TO_BUNDLE
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group_1 = make_alert_group(alert_receive_channel=alert_receive_channel)
    alert_group_2 = make_alert_group(alert_receive_channel=alert_receive_channel)
    now = timezone.now()
    outdated_eta = now - timezone.timedelta(minutes=5)
    test_task_id = "test_task_id"
    notification_bundle = make_user_notification_bundle(
        user,
        UserNotificationPolicy.NotificationChannel.SMS,
        eta=outdated_eta,
        notification_task_id=test_task_id,
        last_notified_at=now,
    )
    notification_bundle.append_notification(alert_group_1, notification_policy)
    assert not notification_bundle.eta_is_valid()
    assert notification_bundle.notifications.count() == 1

    # call notify_user_task and check that new notification task for notification_bundle was scheduled
    notify_user_task(user.id, alert_group_2.id)
    notification_bundle.refresh_from_db()
    assert notification_bundle.eta_is_valid()
    assert notification_bundle.notification_task_id != test_task_id
    assert notification_bundle.last_notified_at == now
    assert notification_bundle.notifications.count() == 2


@patch.object(perform_notification, "apply_async")
@pytest.mark.django_db
def test_notify_user_task_direct_paging_acknowledged(
    mock_perform_notification_apply_async,
    make_organization,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
    make_user_notification_policy,
    django_capture_on_commit_callbacks,
):
    organization = make_organization()
    from_user = make_user(organization=organization)
    user1 = make_user(organization=organization)
    user2 = make_user(organization=organization)
    make_user_notification_policy(
        user=user1,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )
    make_user_notification_policy(
        user=user2,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    direct_paging(organization, from_user, "Test", alert_group=alert_group, users=[(user1, False), (user2, False)])
    alert_group.acknowledge_by_user_or_backsync(user1)

    # no notification should be sent for user1 because they have acknowledged the alert group
    with django_capture_on_commit_callbacks(execute=True):
        notify_user_task(user1.pk, alert_group.pk, notify_even_acknowledged=True)

    mock_perform_notification_apply_async.assert_not_called()

    # user2 should receive a notification because they have not acknowledged the alert group
    with django_capture_on_commit_callbacks(execute=True):
        notify_user_task(user2.pk, alert_group.pk, notify_even_acknowledged=True)

    mock_perform_notification_apply_async.assert_called_once()
