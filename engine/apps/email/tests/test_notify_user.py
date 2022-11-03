import socket
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.mail.backends.locmem import EmailBackend

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.email.tasks import notify_user_async
from apps.user_management.subscription_strategy.free_public_beta_subscription_strategy import (
    FreePublicBetaSubscriptionStrategy,
)


@pytest.mark.django_db
def test_notify_user(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_notify_empty_email_host(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = None

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    assert len(mail.outbox) == 0

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_notify_user_bad_smtp_host(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    with patch.object(EmailBackend, "send_messages", side_effect=socket.gaierror):
        notify_user_async(user.pk, alert_group.pk, notification_policy.pk)

    assert len(mail.outbox) == 0

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED


@pytest.mark.django_db
def test_notify_user_no_emails_left(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"

    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    with patch.object(FreePublicBetaSubscriptionStrategy, "emails_left", return_value=0):
        notify_user_async(user.pk, alert_group.pk, notification_policy.pk)

    assert len(mail.outbox) == 0
    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
    assert log_record.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED


@pytest.mark.django_db
def test_notify_user_from_email_oss(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.LICENSE = settings.OPEN_SOURCE_LICENSE_NAME
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"
    settings.EMAIL_HOST_USER = "test@test.com"

    organization = make_organization(stack_slug="example")
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    assert mail.outbox[0].from_email == "test@test.com"


@pytest.mark.django_db
def test_notify_user_from_email_cloud(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.LICENSE = settings.CLOUD_LICENSE_NAME
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"

    organization = make_organization(stack_slug="slug")
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=8,
        important=False,
    )

    notify_user_async(user.pk, alert_group.pk, notification_policy.pk)
    assert mail.outbox[0].from_email == "oncall@slug.grafana.net"
