import pytest

from apps.alerts.models import AlertReceiveChannel, AlertReceiveChannelConnection


@pytest.mark.django_db
def test_connect_channels(make_organization, make_alert_receive_channel):
    organization = make_organization()
    source_channel = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW)
    channel_to_connect_1 = make_alert_receive_channel(organization)
    channel_to_connect_2 = make_alert_receive_channel(organization)

    assert source_channel.connected_alert_receive_channels.count() == 0
    data = [{"id": ch.public_primary_key, "backsync": True} for ch in [channel_to_connect_1, channel_to_connect_2]]
    AlertReceiveChannelConnection.connect_channels(source_channel, data)
    assert source_channel.connected_alert_receive_channels.count() == 2
    for channel in [channel_to_connect_1, channel_to_connect_2]:
        connected_channel = source_channel.connected_alert_receive_channels.get(connected_channel=channel)
        assert connected_channel.backsync is True


@pytest.mark.django_db
def test_disconnect_channels(
    make_organization,
    make_alert_receive_channel,
    make_alert_receive_channel_connection,
):
    organization = make_organization()

    source_channel = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW)
    connected_channel_1 = make_alert_receive_channel(organization)
    make_alert_receive_channel_connection(source_channel, connected_channel_1)
    connected_channel_2 = make_alert_receive_channel(organization)
    make_alert_receive_channel_connection(source_channel, connected_channel_2)
    connected_channel_3 = make_alert_receive_channel(organization)
    make_alert_receive_channel_connection(source_channel, connected_channel_3)

    assert source_channel.connected_alert_receive_channels.count() == 3
    # disconnect connected_channel_1 and connected_channel_2
    data = [ch.public_primary_key for ch in [connected_channel_1, connected_channel_2]]
    AlertReceiveChannelConnection.disconnect_channels(source_channel, data)
    assert source_channel.connected_alert_receive_channels.count() == 1
    assert source_channel.connected_alert_receive_channels.first().connected_channel == connected_channel_3
