import pytest

from apps.alerts.models import Alert


@pytest.mark.django_db
def test_alert_create_default_channel_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert alert.group.channel_filter == channel_filter


@pytest.mark.django_db
def test_alert_create_custom_channel_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_channel_filter(alert_receive_channel, is_default=True)
    other_channel_filter = make_channel_filter(alert_receive_channel)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        channel_filter=other_channel_filter,
    )

    assert alert.group.channel_filter == other_channel_filter
