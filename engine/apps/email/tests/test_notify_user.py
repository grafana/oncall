import socket
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.mail.backends.locmem import EmailBackend

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.email.alert_rendering import build_subject_and_message
from apps.email.tasks import get_from_email, notify_user_async
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
@pytest.mark.parametrize(
    "license_name,email_host_user,email_from_address,expected",
    [
        ("Cloud", "user", "from_address", "from_address"),
        ("OpenSource", "user", "from_address", "from_address"),
        ("Cloud", "user", None, "oncall@slug.grafana.net"),
        ("Cloud", None, None, "oncall@slug.grafana.net"),
        ("OpenSource", "user", None, "user"),
        ("OpenSource", None, None, None),
    ],
)
def test_get_from_email(
    settings,
    make_organization,
    make_user_for_organization,
    license_name,
    email_host_user,
    email_from_address,
    expected,
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "test"
    settings.EMAIL_HOST_PASSWORD = "password"

    settings.LICENSE = license_name
    settings.EMAIL_HOST_USER = email_host_user
    settings.EMAIL_FROM_ADDRESS = email_from_address

    organization = make_organization(stack_slug="slug")
    user = make_user_for_organization(organization)

    assert get_from_email(user) == expected


@pytest.mark.django_db
def test_subject_newlines_removed(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, messaging_backends_templates={"EMAIL": {"title": "test\nnewlines"}}
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    subject, _ = build_subject_and_message(alert_group, 1)
    assert subject == "[testnewlines] You are invited to check an alert group"
