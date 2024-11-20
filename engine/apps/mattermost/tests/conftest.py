import pytest

from apps.mattermost.tests.factories import MattermostMessageFactory, MattermostUserFactory


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
    def _make_mattermost_post_response(**kwargs):
        return {
            "id": kwargs["id"] if "id" in kwargs else "bew5wsjnctbt78mkq9z6ci9sme",
            "channel_id": kwargs["channel_id"] if "channel_id" in kwargs else "cew5wstyetbt78mkq9z6ci9spq",
            "user_id": kwargs["user_id"] if "user_id" in kwargs else "uew5wsjnctbz78mkq9z6ci9sos",
        }

    return _make_mattermost_post_response


@pytest.fixture()
def make_mattermost_post_response_failure():
    def _make_mattermost_post_response(**kwargs):
        return {
            "status_code": kwargs["status_code"] if "status_code" in kwargs else 400,
            "id": kwargs["id"] if "id" in kwargs else "itre5wsjnctbz78mkq9z6ci9itue",
            "message": kwargs["message"] if "message" in kwargs else "API Error",
            "request_id": kwargs["request_id"] if "request_id" in kwargs else "reqe5wsjnctbz78mkq9z6ci9iqer",
        }

    return _make_mattermost_post_response


@pytest.fixture()
def make_mattermost_message():
    def _make_mattermost_message(alert_group, message_type, **kwargs):
        return MattermostMessageFactory(alert_group=alert_group, message_type=message_type, **kwargs)

    return _make_mattermost_message


@pytest.fixture()
def make_mattermost_user():
    def _make_mattermost_user(user, **kwargs):
        return MattermostUserFactory(user=user, **kwargs)

    return _make_mattermost_user


@pytest.fixture
def set_random_mattermost_sigining_secret(settings):
    def _set_random_mattermost_sigining_secret():
        settings.MATTERMOST_SIGNING_SECRET = "n0cb4954bec053e6e616febf2c2392ff60bd02c453a52ab53d9a8b0d0d6284a6"

    return _set_random_mattermost_sigining_secret


@pytest.fixture()
def make_mattermost_event():
    def _make_mattermost_event(action, token, **kwargs):
        return {
            "user_id": kwargs["user_id"] if "user_id" in kwargs else "k8y8fccx57ygpq18oxp8pp3ntr",
            "user_name": kwargs["user_name"] if "user_name" in kwargs else "hbx80530",
            "channel_id": kwargs["channel_id"] if "channel_id" in kwargs else "gug81e7stfy8md747sewpeeqga",
            "channel_name": kwargs["channel_name"] if "channel_name" in kwargs else "camelcase",
            "team_id": kwargs["team_id"] if "team_id" in kwargs else "kjywdxcbjiyyupdgqst8bj8zrw",
            "team_domain": kwargs["team_domain"] if "team_domain" in kwargs else "local",
            "post_id": kwargs["post_id"] if "post_id" in kwargs else "cfsogqc61fbj3yssz78b1tarbw",
            "trigger_id": kwargs["trigger_id"]
            if "trigger_id" in kwargs
            else (
                "cXJhd2Zwc2V3aW5nanBjY2I2YzdxdTc5NmE6azh5OGZjY3"
                "g1N3lncHExOG94cDhwcDNudHI6MTcyODgyMzQxODU4NzpNRVFDSUgv"
                "bURORjQrWFB1R1QzWHdTWGhDZG9rdEpNb3cydFNJL3l5QktLMkZrVj"
                "dBaUFaMjdybFB3c21EWUlyMHFIeVpKVnIyR1gwa2N6RzY5YkpuSDdrOEpuVXhnPT0="
            ),
            "type": kwargs["type"] if "type" in kwargs else "",
            "data_source": kwargs["data_source"] if "data_source" in kwargs else "",
            "context": {
                "action": action,
                "token": token,
                "alert": kwargs["alert"] if "alert" in kwargs else "",
            },
        }

    return _make_mattermost_event
