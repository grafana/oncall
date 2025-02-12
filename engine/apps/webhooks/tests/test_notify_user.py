from unittest.mock import patch

import pytest
from django.conf import settings

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.webhooks.models import Webhook
from apps.webhooks.tasks import notify_user_async


@pytest.mark.django_db
def test_notify_user_not_found(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy,
    caplog,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=settings.PERSONAL_WEBHOOK_BACKEND_ID,
        important=False,
    )

    with patch("apps.webhooks.tasks.execute_webhook") as mock_execute_webhook:
        notify_user_async(42, alert_group.pk, notification_policy.pk)

    assert mock_execute_webhook.apply_async.called is False
    assert "User 42 does not exist" in caplog.text


@pytest.mark.django_db
def test_notify_user_alert_group_not_found(
    make_organization,
    make_user_for_organization,
    make_user_notification_policy,
    caplog,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=settings.PERSONAL_WEBHOOK_BACKEND_ID,
        important=False,
    )

    with patch("apps.webhooks.tasks.execute_webhook") as mock_execute_webhook:
        notify_user_async(user.pk, 42, notification_policy.pk)

    assert mock_execute_webhook.apply_async.called is False
    assert "Alert group 42 does not exist" in caplog.text


@pytest.mark.django_db
def test_notify_user_policy_not_found(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    caplog,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    with patch("apps.webhooks.tasks.execute_webhook") as mock_execute_webhook:
        notify_user_async(user.pk, alert_group.pk, 42)

    assert mock_execute_webhook.apply_async.called is False
    assert "User notification policy 42 does not exist" in caplog.text


@pytest.mark.django_db
def test_notify_user_personal_webhook_not_set(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy,
    caplog,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=settings.PERSONAL_WEBHOOK_BACKEND_ID,
        important=False,
    )

    with patch("apps.webhooks.tasks.execute_webhook") as mock_execute_webhook:
        notify_user_async(user.pk, alert_group.pk, notification_policy.pk)

    assert mock_execute_webhook.apply_async.called is False
    assert f"Personal webhook is not set for user {user.pk}" in caplog.text
    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_notify_user_ok(
    make_organization,
    make_user_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy,
    make_custom_webhook,
    make_personal_notification_webhook,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    # set personal webhook
    webhook = make_custom_webhook(
        organization=organization,
        trigger_type=Webhook.TRIGGER_PERSONAL_NOTIFICATION,
    )
    make_personal_notification_webhook(user=user, webhook=webhook)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=settings.PERSONAL_WEBHOOK_BACKEND_ID,
        important=False,
    )

    with patch("apps.webhooks.tasks.execute_webhook") as mock_execute_webhook:
        notify_user_async(user.pk, alert_group.pk, notification_policy.pk)

    mock_execute_webhook.apply_async.assert_called_once_with(
        (user.personal_webhook.webhook.pk, alert_group.pk, user.pk, notification_policy.pk),
        kwargs={"trigger_type": Webhook.TRIGGER_PERSONAL_NOTIFICATION},
    )

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


# tests: user does not exist, ag does not exist, policy does not exist; no webhook; webhook triggered
