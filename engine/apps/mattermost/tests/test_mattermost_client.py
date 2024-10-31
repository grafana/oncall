import json
from unittest.mock import Mock, patch

import httpretty
import pytest
import requests
from django.conf import settings
from rest_framework import status

from apps.mattermost.client import MattermostAPIException, MattermostAPITokenInvalid, MattermostClient


@pytest.mark.django_db
def test_mattermost_client_initialization():
    settings.MATTERMOST_BOT_TOKEN = None
    with pytest.raises(MattermostAPITokenInvalid) as exc:
        MattermostClient()
        assert type(exc) is MattermostAPITokenInvalid


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_get_channel_by_id_ok(make_mattermost_get_channel_response):
    client = MattermostClient("abcd")
    data = make_mattermost_get_channel_response()
    url = "{}/api/v4/channels/{}".format(settings.MATTERMOST_HOST, data["id"])

    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.GET, url, responses=[mock_response])

    channel_response = client.get_channel_by_id(data["id"])

    last_request = httpretty.last_request()
    assert last_request.method == "GET"
    assert last_request.url == url
    assert channel_response.channel_id == data["id"]
    assert channel_response.team_id == data["team_id"]
    assert channel_response.channel_name == data["name"]
    assert channel_response.display_name == data["display_name"]


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_get_user_ok(make_mattermost_get_user_response):
    client = MattermostClient("abcd")
    data = make_mattermost_get_user_response()
    url = "{}/api/v4/users/{}".format(settings.MATTERMOST_HOST, data["id"])

    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.GET, url, responses=[mock_response])

    mattermost_user = client.get_user(data["id"])

    last_request = httpretty.last_request()
    assert last_request.method == "GET"
    assert last_request.url == url
    assert mattermost_user.user_id == data["id"]
    assert mattermost_user.username == data["username"]
    assert mattermost_user.nickname == data["nickname"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "client_method,params,method",
    [
        ("get_channel_by_id", ["fuzz"], "GET"),
        ("get_user", ["fuzz"], "GET"),
        ("create_post", ["fuzz", {}], "POST"),
        ("update_post", ["fuzz", {}], "PUT"),
    ],
)
def test_check_response_failures(client_method, params, method):
    client = MattermostClient("abcd")
    data = {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "id": "fuzzbuzz",
        "message": "Client Error",
        "request_id": "foobar",
    }

    # HTTP Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_400_BAD_REQUEST
    mock_response.json.return_value = data
    mock_response.request = requests.Request(
        url="https://example.com",
        method=method,
    )
    mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
    with patch(f"apps.mattermost.client.requests.{method.lower()}", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            getattr(client, client_method)(*params)
        mock_request.assert_called_once()

    # Timeout Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.request = requests.Request(
        url="https://example.com",
        method=method,
    )
    mock_response.raise_for_status.side_effect = requests.Timeout(response=mock_response)
    with patch(f"apps.mattermost.client.requests.{method.lower()}", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            getattr(client, client_method)(*params)
        assert exc.value.msg == "Mattermost api call gateway timedout"
        mock_request.assert_called_once()

    # RequestException Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.request = requests.Request(
        url="https://example.com",
        method=method,
    )
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException(response=mock_response)
    with patch(f"apps.mattermost.client.requests.{method.lower()}", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            getattr(client, client_method)(*params)
        assert exc.value.msg == "Unexpected error from mattermost server"
        mock_request.assert_called_once()


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_create_post_ok(make_mattermost_post_response):
    client = MattermostClient("abcd")
    data = make_mattermost_post_response()
    url = "{}/api/v4/posts".format(settings.MATTERMOST_HOST)

    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.POST, url, responses=[mock_response])

    mattermost_post = client.create_post(data["id"], {})

    last_request = httpretty.last_request()
    assert last_request.method == "POST"
    assert last_request.url == url
    assert mattermost_post.post_id == data["id"]
    assert mattermost_post.channel_id == data["channel_id"]
    assert mattermost_post.user_id == data["user_id"]


@pytest.mark.django_db
@httpretty.activate(verbose=True, allow_net_connect=False)
def test_update_post_ok(make_mattermost_post_response):
    client = MattermostClient("abcd")
    data = make_mattermost_post_response()
    url = "{}/api/v4/posts/{}".format(settings.MATTERMOST_HOST, data["id"])

    mock_response = httpretty.Response(json.dumps(data), status=status.HTTP_200_OK)
    httpretty.register_uri(httpretty.PUT, url, responses=[mock_response])

    mattermost_post = client.update_post(data["id"], {})

    last_request = httpretty.last_request()
    assert last_request.method == "PUT"
    assert last_request.url == url
    assert mattermost_post.post_id == data["id"]
    assert mattermost_post.channel_id == data["channel_id"]
    assert mattermost_post.user_id == data["user_id"]
