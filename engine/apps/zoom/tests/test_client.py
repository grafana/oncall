import pytest
import responses
from django.conf import settings
from django.test import override_settings

# Skip all tests if Zoom integration is not enabled
if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
    pytest.skip("Zoom integration is not enabled", allow_module_level=True)


@pytest.mark.django_db
@responses.activate
@override_settings(
    ZOOM_BOT_TOKEN="test_token",
    ZOOM_ROBOT_JID="robot@xmpp.zoom.us",
    ZOOM_ACCOUNT_ID="account123",
)
def test_zoom_client_get_channel(make_zoom_get_channel_response):
    """Test ZoomClient.get_channel method."""
    from apps.zoom.client import ZoomClient

    channel_id = "channel123"
    responses.add(
        responses.GET,
        f"https://api.zoom.us/v2/chat/channels/{channel_id}",
        json=make_zoom_get_channel_response(),
        status=200,
    )

    client = ZoomClient()
    result = client.get_channel(channel_id)

    assert result.channel_id == "pbg5piuc5bgniftrserb88575h"
    assert result.channel_name == "General Channel"


@pytest.mark.django_db
@responses.activate
@override_settings(
    ZOOM_BOT_TOKEN="test_token",
    ZOOM_ROBOT_JID="robot@xmpp.zoom.us",
    ZOOM_ACCOUNT_ID="account123",
)
def test_zoom_client_send_channel_message(make_zoom_message_response):
    """Test ZoomClient.send_channel_message method."""
    from apps.zoom.client import ZoomClient

    channel_id = "channel123"
    responses.add(
        responses.POST,
        "https://api.zoom.us/v2/im/chat/messages",
        json=make_zoom_message_response(),
        status=200,
    )

    client = ZoomClient()
    result = client.send_channel_message(
        channel_id=channel_id,
        message="Test message",
    )

    assert result.message_id == "bew5wsjnctbt78mkq9z6ci9sme"
    assert result.to_channel == channel_id


@pytest.mark.django_db
@responses.activate
@override_settings(
    ZOOM_BOT_TOKEN="test_token",
    ZOOM_ROBOT_JID="robot@xmpp.zoom.us",
    ZOOM_ACCOUNT_ID="account123",
)
def test_zoom_client_update_message(make_zoom_message_response):
    """Test ZoomClient.update_message method."""
    from apps.zoom.client import ZoomClient

    message_id = "msg123"
    channel_id = "channel123"
    responses.add(
        responses.PUT,
        f"https://api.zoom.us/v2/im/chat/messages/{message_id}",
        json=make_zoom_message_response(message_id=message_id),
        status=200,
    )

    client = ZoomClient()
    result = client.update_message(
        message_id=message_id,
        channel_id=channel_id,
        message="Updated message",
    )

    assert result.message_id == message_id
    assert result.to_channel == channel_id


@pytest.mark.django_db
@override_settings(ZOOM_BOT_TOKEN=None)
def test_zoom_client_missing_token():
    """Test ZoomClient raises error when token is missing."""
    from apps.zoom.client import ZoomClient
    from apps.zoom.exceptions import ZoomAPITokenInvalid

    with pytest.raises(ZoomAPITokenInvalid):
        ZoomClient()


@pytest.mark.django_db
@responses.activate
@override_settings(
    ZOOM_BOT_TOKEN="test_token",
    ZOOM_ROBOT_JID="robot@xmpp.zoom.us",
    ZOOM_ACCOUNT_ID="account123",
)
def test_zoom_client_api_error():
    """Test ZoomClient handles API errors correctly."""
    from apps.zoom.client import ZoomClient
    from apps.zoom.exceptions import ZoomAPIException

    channel_id = "channel123"
    responses.add(
        responses.GET,
        f"https://api.zoom.us/v2/chat/channels/{channel_id}",
        json={"code": 404, "message": "Channel not found"},
        status=404,
    )

    client = ZoomClient()
    with pytest.raises(ZoomAPIException):
        client.get_channel(channel_id)
