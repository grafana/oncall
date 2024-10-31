import pytest

from apps.mattermost.tests.factories import MattermostMessageFactory


@pytest.fixture()
def make_mattermost_get_channel_response():
    def _make_mattermost_get_channel_response():
        return {
            "id": "pbg5piuc5bgniftrserb88575h",
            "team_id": "oxfug4kgx3fx7jzow49cpxkmgo",
            "display_name": "Town Square",
            "name": "town-square",
        }

    return _make_mattermost_get_channel_response


@pytest.fixture()
def make_mattermost_get_user_response():
    def _make_mattermost_get_user_response():
        return {
            "id": "bew5wsjnctbt78mkq9z6ci9sme",
            "username": "fuzz",
            "nickname": "buzz",
        }

    return _make_mattermost_get_user_response


@pytest.fixture()
def make_mattermost_post_response():
    def _make_mattermost_post_response():
        return {
            "id": "bew5wsjnctbt78mkq9z6ci9sme",
            "channel_id": "cew5wstyetbt78mkq9z6ci9spq",
            "user_id": "uew5wsjnctbz78mkq9z6ci9sos",
        }

    return _make_mattermost_post_response


@pytest.fixture()
def make_mattermost_post_response_failure():
    def _make_mattermost_post_response(**kwargs):
        return {
            "status_code": kwargs["status_code"] if "status_code" in kwargs else 400,
            "id": kwargs["id"] if "id" in kwargs else "itre5wsjnctbz78mkq9z6ci9itue",
            "message": kwargs["message"] if "message" in kwargs else "API Error",
            "request_id": kwargs["message"] if "message" in kwargs else "reqe5wsjnctbz78mkq9z6ci9iqer",
        }

    return _make_mattermost_post_response


@pytest.fixture()
def make_mattermost_message():
    def _make_mattermost_message(alert_group, message_type, **kwargs):
        return MattermostMessageFactory(alert_group=alert_group, message_type=message_type, **kwargs)

    return _make_mattermost_message
