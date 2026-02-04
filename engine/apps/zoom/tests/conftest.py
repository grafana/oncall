import pytest
from django.conf import settings

# Skip all tests in this module if Zoom integration is not enabled
if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
    pytest.skip("Zoom integration is not enabled", allow_module_level=True)
else:
    from apps.zoom.tests.factories import (
        ZoomChannelFactory,
        ZoomMessageFactory,
        ZoomUserFactory,
    )


@pytest.fixture()
def make_zoom_channel():
    def _make_zoom_channel(organization, **kwargs):
        return ZoomChannelFactory(organization=organization, **kwargs)

    return _make_zoom_channel


@pytest.fixture()
def make_zoom_get_channel_response():
    def _make_zoom_get_channel_response():
        return {
            "id": "pbg5piuc5bgniftrserb88575h",
            "name": "General Channel",
            "type": 1,
        }

    return _make_zoom_get_channel_response


@pytest.fixture()
def make_zoom_get_user_response():
    def _make_zoom_get_user_response():
        return {
            "id": "bew5wsjnctbt78mkq9z6ci9sme",
            "email": "user@example.com",
            "display_name": "Test User",
            "first_name": "Test",
            "last_name": "User",
        }

    return _make_zoom_get_user_response


@pytest.fixture()
def make_zoom_message_response():
    def _make_zoom_message_response(**kwargs):
        return {
            "message_id": kwargs.get("message_id", "bew5wsjnctbt78mkq9z6ci9sme"),
            "to_channel": kwargs.get("to_channel", "cew5wstyetbt78mkq9z6ci9spq"),
            "robot_jid": kwargs.get("robot_jid", "robot@xmpp.zoom.us"),
        }

    return _make_zoom_message_response


@pytest.fixture()
def make_zoom_message():
    def _make_zoom_message(alert_group, message_type, **kwargs):
        return ZoomMessageFactory(alert_group=alert_group, message_type=message_type, **kwargs)

    return _make_zoom_message


@pytest.fixture()
def make_zoom_user():
    def _make_zoom_user(user, **kwargs):
        return ZoomUserFactory(user=user, **kwargs)

    return _make_zoom_user


@pytest.fixture
def set_zoom_signing_secret(settings):
    def _set_zoom_signing_secret():
        settings.ZOOM_SIGNING_SECRET = "n0cb4954bec053e6e616febf2c2392ff60bd02c453a52ab53d9a8b0d0d6284a6"

    return _set_zoom_signing_secret


@pytest.fixture()
def make_zoom_interactive_event():
    def _make_zoom_interactive_event(action, alert_pk, token, **kwargs):
        return {
            "accountId": kwargs.get("account_id", "account123"),
            "channelName": kwargs.get("channel_name", "General Channel"),
            "robotJid": kwargs.get("robot_jid", "robot@xmpp.zoom.us"),
            "toJid": kwargs.get("to_jid", "channel@conference.xmpp.zoom.us"),
            "userId": kwargs.get("user_id", "k8y8fccx57ygpq18oxp8pp3ntr"),
            "userJid": kwargs.get("user_jid", "user@xmpp.zoom.us"),
            "userName": kwargs.get("user_name", "Test User"),
            "messageId": kwargs.get("message_id", "msg123"),
            "timestamp": kwargs.get("timestamp", 1728823418587),
            "actionItem": {
                "text": kwargs.get("button_text", "Acknowledge"),
                "value": f"{action}|{alert_pk}|{token}",
                "style": kwargs.get("style", "Primary"),
            },
        }

    return _make_zoom_interactive_event
