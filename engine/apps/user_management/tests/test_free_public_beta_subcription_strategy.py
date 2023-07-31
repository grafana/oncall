import pytest

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_phone_calls_left(
    make_organization,
    make_user_for_organization,
    make_phone_call_record,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_phone_call_record(receiver=admin, represents_alert_group=alert_group)

    assert organization.phone_calls_left(admin) == organization.subscription_strategy._phone_notifications_limit - 1
    assert organization.phone_calls_left(user) == organization.subscription_strategy._phone_notifications_limit


@pytest.mark.django_db
def test_sms_left(
    make_organization, make_user_for_organization, make_sms_record, make_alert_receive_channel, make_alert_group
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_sms_record(receiver=admin, represents_alert_group=alert_group)

    assert organization.sms_left(admin) == organization.subscription_strategy._phone_notifications_limit - 1
    assert organization.sms_left(user) == organization.subscription_strategy._phone_notifications_limit


@pytest.mark.django_db
def test_phone_calls_and_sms_counts_together(
    make_organization,
    make_user_for_organization,
    make_phone_call_record,
    make_sms_record,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_phone_call_record(receiver=admin, represents_alert_group=alert_group)
    make_sms_record(receiver=admin, represents_alert_group=alert_group)

    assert organization.phone_calls_left(admin) == organization.subscription_strategy._phone_notifications_limit - 2
    assert organization.sms_left(admin) == organization.subscription_strategy._phone_notifications_limit - 2

    assert organization.phone_calls_left(user) == organization.subscription_strategy._phone_notifications_limit
    assert organization.sms_left(user) == organization.subscription_strategy._phone_notifications_limit


@pytest.mark.django_db
def test_emails_left(
    make_organization,
    make_user_for_organization,
    make_email_message,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    user = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_email_message(receiver=user, represents_alert_group=alert_group)

    assert organization.emails_left(user) == organization.subscription_strategy._emails_limit - 1
