import pytest
from django.conf import settings

# Skip all tests if Zoom integration is not enabled
if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
    pytest.skip("Zoom integration is not enabled", allow_module_level=True)


@pytest.mark.django_db
def test_zoom_channel_get_channel_for_alert_group_default(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_zoom_channel,
):
    """Test that default channel is returned when no specific channel is configured."""
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel=alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel, channel_filter=channel_filter)

    # Create a default Zoom channel
    default_channel = make_zoom_channel(organization=organization, is_default_channel=True)

    from apps.zoom.models import ZoomChannel
    result = ZoomChannel.get_channel_for_alert_group(alert_group)

    assert result == default_channel


@pytest.mark.django_db
def test_zoom_channel_make_channel_default(
    make_organization,
    make_user_for_organization,
    make_zoom_channel,
):
    """Test making a channel the default channel."""
    organization = make_organization()
    user = make_user_for_organization(organization)

    channel1 = make_zoom_channel(organization=organization, is_default_channel=True)
    channel2 = make_zoom_channel(organization=organization, is_default_channel=False)

    channel2.make_channel_default(user)
    channel1.refresh_from_db()
    channel2.refresh_from_db()

    assert channel1.is_default_channel is False
    assert channel2.is_default_channel is True


@pytest.mark.django_db
def test_zoom_user_mention_format(
    make_organization,
    make_user_for_organization,
    make_zoom_user,
):
    """Test Zoom user mention format."""
    organization = make_organization()
    user = make_user_for_organization(organization)
    zoom_user = make_zoom_user(user=user, email="test@example.com", display_name="Test User")

    expected_mention = '<at email="test@example.com">Test User</at>'
    assert zoom_user.mention_format == expected_mention


@pytest.mark.django_db
def test_zoom_message_create_message(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    """Test ZoomMessage.create_message static method."""
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    from apps.zoom.models import ZoomMessage
    message = ZoomMessage.create_message(
        alert_group=alert_group,
        message_id="test_msg_123",
        channel_id="test_channel_456",
        message_type=ZoomMessage.ALERT_GROUP_MESSAGE,
    )

    assert message.message_id == "test_msg_123"
    assert message.channel_id == "test_channel_456"
    assert message.message_type == ZoomMessage.ALERT_GROUP_MESSAGE
    assert message.alert_group == alert_group
