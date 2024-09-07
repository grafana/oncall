import json
from unittest.mock import Mock, patch

import pytest
import requests
from rest_framework import status

from apps.base.utils import live_settings
from apps.mattermost.client import MattermostAPIException, MattermostAPITokenInvalid, MattermostClient


@pytest.mark.django_db
def test_mattermost_client_initialization():
    live_settings.MATTERMOST_BOT_TOKEN = None
    with pytest.raises(MattermostAPITokenInvalid) as exc:
        MattermostClient()
        assert type(exc) is MattermostAPITokenInvalid


@pytest.mark.django_db
def test_get_channel_by_name_and_team_name_ok(make_mattermost_get_channel_by_name_team_name_response):
    client = MattermostClient("abcd")
    data = make_mattermost_get_channel_by_name_team_name_response()
    channel_response = requests.Response()
    channel_response.status_code = status.HTTP_200_OK
    channel_response._content = json.dumps(data).encode()
    with patch("apps.mattermost.client.requests.get", return_value=channel_response) as mock_request:
        response = client.get_channel_by_name_and_team_name("test-team", "test-channel")
        mock_request.assert_called_once()
        assert response.channel_id == data["id"]
        assert response.team_id == data["team_id"]
        assert response.display_name == data["display_name"]
        assert response.channel_name == data["name"]


@pytest.mark.django_db
def test_get_channel_by_name_and_team_name_failure():
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
        method="GET",
    )
    mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
    with patch("apps.mattermost.client.requests.get", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            client.get_channel_by_name_and_team_name("test-team", "test-channel")
        mock_request.assert_called_once()

    # Timeout Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.request = requests.Request(
        url="https://example.com",
        method="GET",
    )
    mock_response.raise_for_status.side_effect = requests.Timeout(response=mock_response)
    with patch("apps.mattermost.client.requests.get", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            client.get_channel_by_name_and_team_name("test-team", "test-channel")
        assert exc.value.msg == "Mattermost api call gateway timedout"
        mock_request.assert_called_once()

    # RequestException Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.request = requests.Request(
        url="https://example.com",
        method="GET",
    )
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException(response=mock_response)
    with patch("apps.mattermost.client.requests.get", return_value=mock_response) as mock_request:
        with pytest.raises(MattermostAPIException) as exc:
            client.get_channel_by_name_and_team_name("test-team", "test-channel")
        assert exc.value.msg == "Unexpected error from mattermost server"
        mock_request.assert_called_once()
