import copy

import pytest

from apps.alerts.models import AlertGroupLogRecord, AlertReceiveChannel
from apps.telegram.renderers.message import MAX_TELEGRAM_MESSAGE_LENGTH, MESSAGE_TRIMMED_TEXT, TelegramMessageRenderer


@pytest.mark.django_db
def test_alert_group_message_too_long_is_trimmed(
    make_organization, make_alert_receive_channel, make_alert_group, make_alert
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)

    payload = copy.deepcopy(alert_receive_channel.config.tests["payload"])
    payload["labels"]["test"] = "test" * 2000

    make_alert(alert_group=alert_group, raw_request_data=payload)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_alert_group_message()

    assert len(text) <= MAX_TELEGRAM_MESSAGE_LENGTH
    assert text.endswith(MESSAGE_TRIMMED_TEXT.format(link=alert_group.web_link))


@pytest.mark.django_db
def test_log_message(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization, user = make_organization_and_user()
    user_name = user.get_username_with_slack_verbal()

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    default_channel_filter.escalation_chain = make_escalation_chain(organization, name="test")

    alert_group = make_alert_group(alert_receive_channel, channel_filter=default_channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    make_alert_group_log_record(alert_group=alert_group, author=user, type=AlertGroupLogRecord.TYPE_ACK)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_log_message()

    assert text == f"Alert group log:\n<b>0s:</b> acknowledged by {user_name}"


@pytest.mark.django_db
def test_alert_group_message(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.tests["payload"])

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_alert_group_message()
    assert text == (
        f"<a href='{organization.web_link_with_uuid}'>&#8205;</a>🔴 #{alert_group.inside_organization_number}, {alert_receive_channel.config.tests['telegram']['title']}\n"
        "Firing, alerts: 1\n"
        "Source: Test integration - Grafana\n"
        f"{alert_group.web_link}\n\n"
        f"{alert_receive_channel.config.tests['telegram']['message']}"
    )


@pytest.mark.django_db
def test_log_message_too_long_is_trimmed(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization, user = make_organization_and_user()
    user_name = user.get_username_with_slack_verbal()

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert_group = make_alert_group(alert_receive_channel, channel_filter=default_channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    for _ in range(300):
        make_alert_group_log_record(alert_group=alert_group, author=user, type=AlertGroupLogRecord.TYPE_RESOLVED)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_log_message()

    assert len(text) <= MAX_TELEGRAM_MESSAGE_LENGTH

    end_text = f"resolved by {user_name}" + MESSAGE_TRIMMED_TEXT.format(link=alert_group.web_link)
    assert text.endswith(end_text)


@pytest.mark.django_db
def test_actions_message(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_actions_message()

    assert text == "Actions available for this alert group"


@pytest.mark.django_db
def test_personal_message(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
    make_alert,
):
    organization, user = make_organization_and_user()
    user_name = user.get_username_with_slack_verbal()

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    default_channel_filter.escalation_chain = make_escalation_chain(organization, name="test")

    alert_group = make_alert_group(alert_receive_channel, channel_filter=default_channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.tests["payload"])

    alert_group.acknowledge_by_user(user)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_personal_message()

    assert text == (
        f"<a href='{organization.web_link_with_uuid}'>&#8205;</a>🟠 #{alert_group.inside_organization_number}, {alert_receive_channel.config.tests['telegram']['title']}\n"
        f"Acknowledged by {user_name}, alerts: 1\n"
        "Source: Test integration - Grafana\n"
        f"{alert_group.web_link}\n\n"
        f"{alert_receive_channel.config.tests['telegram']['message']}\n\n\n"
        "Alert group log:\n"
        f"<b>0s:</b> acknowledged by {user_name}"
    )


@pytest.mark.django_db
def test_link_to_channel_message(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.tests["payload"])

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_link_to_channel_message()

    assert text == (
        f"👀 You are invited to look at an alert group!\n"
        f"<b>#{alert_group.inside_organization_number}, {alert_receive_channel.config.tests['telegram']['title']}</b>"
    )


@pytest.mark.django_db
def test_formatting_error_message(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )

    alert_group = make_alert_group(alert_receive_channel)

    renderer = TelegramMessageRenderer(alert_group=alert_group)
    text = renderer.render_formatting_error_message()

    assert text == (
        "You have a new alert group, but Telegram can't render its content! "
        f"Please check it out: {alert_group.web_link}"
    )
