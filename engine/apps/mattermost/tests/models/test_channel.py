import pytest

from apps.mattermost.models import MattermostChannel


@pytest.mark.django_db
def test_get_channel_for_alert_group(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_mattermost_channel(organization=organization, is_default_channel=True)
    channel = make_mattermost_channel(organization=organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        notification_backends={"MATTERMOST": {"channel": channel.public_primary_key, "enabled": True}},
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    ch = MattermostChannel.get_channel_for_alert_group(alert_group)
    assert ch.public_primary_key == channel.public_primary_key


@pytest.mark.django_db
def test_get_mattermost_channel_disabled_for_route(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel = make_mattermost_channel(organization=organization, is_default_channel=True)
    channel = make_mattermost_channel(organization=organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        notification_backends={"MATTERMOST": {"channel": channel.public_primary_key, "enabled": False}},
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    ch = MattermostChannel.get_channel_for_alert_group(alert_group)
    assert ch.public_primary_key == default_channel.public_primary_key


@pytest.mark.django_db
def test_get_mattermost_channel_invalid_route_channel(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_mattermost_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel = make_mattermost_channel(organization=organization, is_default_channel=True)
    channel_filter = make_channel_filter(
        alert_receive_channel, notification_backends={"MATTERMOST": {"channel": "invalid_id", "enabled": True}}
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    ch = MattermostChannel.get_channel_for_alert_group(alert_group)
    assert ch.public_primary_key == default_channel.public_primary_key


@pytest.mark.django_db
def test_get_mattermost_channel_channel_filter_not_configured(
    make_organization, make_alert_receive_channel, make_alert_group, make_alert, make_mattermost_channel
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel = make_mattermost_channel(organization=organization, is_default_channel=True)

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    ch = MattermostChannel.get_channel_for_alert_group(alert_group)
    assert ch.public_primary_key == default_channel.public_primary_key
