import json
from unittest.mock import patch

import pytest
import responses
from requests.exceptions import RequestException
from rest_framework import status

from common.incident_api.client import (
    DEFAULT_ACTIVITY_KIND,
    DEFAULT_INCIDENT_SEVERITY,
    DEFAULT_INCIDENT_STATUS,
    IncidentAPIClient,
    IncidentAPIException,
)


@responses.activate
def test_create_incident_expected_request():
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}api/v1/IncidentsService.CreateIncident"
    response_data = {
        "error": "",
        "incident": {
            "incidentID": "123",
        },
    }
    responses.add(responses.POST, url, json=response_data, status=status.HTTP_200_OK)

    title = "title"
    severity = "severity"
    attachCaption = "attachCaption"
    attachURL = "http://some.url"
    incident_status = "active"
    data, response = client.create_incident(title, severity, incident_status, attachCaption, attachURL)

    assert data == response_data["incident"]
    assert response.status_code == status.HTTP_200_OK
    last_request = responses.calls[-1].request
    assert last_request.headers["Authorization"] == f"Bearer {api_token}"
    assert last_request.method == "POST"
    assert last_request.url == url
    assert json.loads(last_request.body) == {
        "title": title,
        "severity": severity,
        "attachCaption": attachCaption,
        "attachURL": attachURL,
        "status": incident_status,
    }

    # test using defaults
    data, response = client.create_incident(title)

    assert data == response_data["incident"]
    assert response.status_code == status.HTTP_200_OK
    last_request = responses.calls[-1].request
    assert json.loads(last_request.body) == {
        "title": title,
        "severity": DEFAULT_INCIDENT_SEVERITY,
        "attachCaption": "",
        "attachURL": "",
        "status": DEFAULT_INCIDENT_STATUS,
    }


@responses.activate
def test_get_incident_expected_request():
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}api/v1/IncidentsService.GetIncident"
    incident_id = "123"
    response_data = {
        "error": "",
        "incident": {
            "incidentID": incident_id,
        },
    }
    responses.add(responses.POST, url, json=response_data, status=status.HTTP_200_OK)

    data, response = client.get_incident(incident_id)

    assert data == response_data["incident"]
    assert response.status_code == status.HTTP_200_OK
    last_request = responses.calls[-1].request
    assert last_request.headers["Authorization"] == f"Bearer {api_token}"
    assert last_request.method == "POST"
    assert last_request.url == url


@responses.activate
def test_get_severities_expected_request():
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}api/SeveritiesService.GetOrgSeverities"
    response_data = {
        "error": "",
        "severities": [
            {"severityID": "abc", "orgID": "1", "displayLabel": "Pending", "level": -1},
            {"severityID": "def", "orgID": "1", "displayLabel": "Critical", "level": 1},
        ],
    }
    responses.add(responses.POST, url, json=response_data, status=status.HTTP_200_OK)

    data, response = client.get_severities()

    assert data == response_data["severities"]
    assert response.status_code == status.HTTP_200_OK
    last_request = responses.calls[-1].request
    assert last_request.headers["Authorization"] == f"Bearer {api_token}"
    assert last_request.method == "POST"
    assert last_request.url == url
    assert json.loads(last_request.body) == {}


@responses.activate
def test_add_activity_expected_request():
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}api/v1/ActivityService.AddActivity"
    incident_id = "123"
    content = "some content"
    response_data = {
        "error": "",
        "activityItem": {
            "activityItemID": "activity-item-theID",
            "incidentID": incident_id,
            "user": {
                "userID": "grafana-incident:user-user-id",
                "name": "Service Account: extsvc-grafana-oncall-app",
            },
            "createdTime": "2024-09-18T14:06:47.57795Z",
            "activityKind": "userNote",
            "body": content,
        },
    }
    responses.add(responses.POST, url, json=response_data, status=status.HTTP_200_OK)

    data, response = client.add_activity(incident_id, content)

    assert data == response_data["activityItem"]
    assert response.status_code == status.HTTP_200_OK
    last_request = responses.calls[-1].request
    assert last_request.headers["Authorization"] == f"Bearer {api_token}"
    assert last_request.method == "POST"
    assert last_request.url == url
    assert json.loads(last_request.body) == {
        "incidentID": incident_id,
        "activityKind": DEFAULT_ACTIVITY_KIND,
        "body": content,
    }


@pytest.mark.parametrize(
    "endpoint, client_method_name, args",
    [
        ("api/v1/IncidentsService.CreateIncident", "create_incident", ("title",)),
        ("api/v1/IncidentsService.GetIncident", "get_incident", ("incident-id",)),
        ("api/SeveritiesService.GetOrgSeverities", "get_severities", ()),
        ("api/v1/ActivityService.AddActivity", "add_activity", ("incident-id", "content")),
    ],
)
@responses.activate
def test_error_handling(endpoint, client_method_name, args):
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}{endpoint}"
    response_data = {
        "error": "There was an error",
    }
    for error_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR):
        responses.add(responses.POST, url, json=response_data, status=error_code)
        with pytest.raises(IncidentAPIException) as excinfo:
            client_method = getattr(client, client_method_name)
            client_method(*args)
        assert excinfo.value.status == error_code
        assert excinfo.value.msg == response_data["error"]
        assert excinfo.value.url == url
        assert excinfo.value.method == "POST"
        responses.reset()


@pytest.mark.parametrize(
    "endpoint, client_method_name, args",
    [
        ("api/v1/IncidentsService.CreateIncident", "create_incident", ("title",)),
        ("api/v1/IncidentsService.GetIncident", "get_incident", ("incident-id",)),
        ("api/SeveritiesService.GetOrgSeverities", "get_severities", ()),
        ("api/v1/ActivityService.AddActivity", "add_activity", ("incident-id", "content")),
    ],
)
def test_unexpected_error_handling(endpoint, client_method_name, args):
    stack_url = "https://foobar.grafana.net"
    api_token = "asdfasdfasdfasdf"
    client = IncidentAPIClient(stack_url, api_token)
    url = f"{stack_url}{client.INCIDENT_BASE_PATH}{endpoint}"
    with patch("common.incident_api.client.requests.post", side_effect=RequestException):
        with pytest.raises(IncidentAPIException) as excinfo:
            client_method = getattr(client, client_method_name)
            client_method(*args)
        assert excinfo.value.status == 500
        assert excinfo.value.msg == "Unexpected error"
        assert excinfo.value.url == url
        assert excinfo.value.method == "POST"
