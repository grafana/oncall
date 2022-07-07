import pytest

from apps.telegram.models import TelegramMessage, TelegramToOrganizationConnector


@pytest.mark.django_db
def test_get_channel_for_alert_group(
    make_organization, make_alert_receive_channel, make_channel_filter, make_alert_group, make_telegram_channel
):
    organization = make_organization()

    make_telegram_channel(organization, is_default_channel=True)
    telegram_channel = make_telegram_channel(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel, notify_in_telegram=True, telegram_channel=telegram_channel
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    channel = TelegramToOrganizationConnector.get_channel_for_alert_group(alert_group)
    assert channel is telegram_channel


@pytest.mark.django_db
def test_get_channel_telegram_disabled_for_route(
    make_organization, make_alert_receive_channel, make_channel_filter, make_alert_group, make_telegram_channel
):
    organization = make_organization()

    telegram_channel = make_telegram_channel(organization)

    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel, notify_in_telegram=False, telegram_channel=telegram_channel
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    channel = TelegramToOrganizationConnector.get_channel_for_alert_group(alert_group)
    assert channel is None


@pytest.mark.django_db
def test_get_channel_for_alert_group_dm_messages_exist(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_telegram_channel,
    make_telegram_message,
):
    organization = make_organization()

    telegram_channel = make_telegram_channel(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel, notify_in_telegram=True, telegram_channel=telegram_channel
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_telegram_message(alert_group=alert_group, message_type=TelegramMessage.PERSONAL_MESSAGE)

    channel = TelegramToOrganizationConnector.get_channel_for_alert_group(alert_group)
    assert channel is None
