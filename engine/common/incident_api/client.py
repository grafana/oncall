import typing
from json import JSONDecodeError
from urllib.parse import urljoin

import requests
from django.conf import settings
from requests.exceptions import RequestException

from common.constants.plugin_ids import PluginID


class IncidentDetails(typing.TypedDict):
    # https://grafana.com/docs/grafana-cloud/alerting-and-irm/irm/incident/api/reference/#getincidentresponse
    createdByUser: typing.Dict
    createdTime: str
    durationSeconds: int
    heroImagePath: str
    incidentEnd: str
    incidentID: str
    incidentMembership: typing.Dict
    incidentStart: str
    isDrill: bool
    labels: typing.List[dict]
    overviewURL: str
    severity: str
    status: str
    summary: str
    taskList: typing.Dict
    title: str


class SeverityDetails(typing.TypedDict):
    severityID: str
    orgID: str
    displayLabel: str
    level: int
    iconName: str
    description: str
    darkColor: str
    lightColor: str
    archivedAt: str
    archivedByUserID: str | None
    deletedAt: str
    deletedByUserID: str | None
    createdAt: str
    updatedAt: str


class ActivityItemDetails(typing.TypedDict):
    # https://grafana.com/docs/grafana-cloud/alerting-and-irm/irm/incident/api/reference/#addactivityresponse
    activityItemID: str
    activityKind: str
    attachments: typing.List[dict]
    body: str
    createdTime: str
    eventTime: str
    fieldValues: typing.Dict[str, str]
    immutable: bool
    incidentID: str
    relevance: str
    subjectUser: typing.Dict[str, str]
    tags: typing.List[str]
    url: str
    user: typing.Dict[str, str]


class IncidentAPIException(Exception):
    def __init__(self, status, url, msg="", method="GET"):
        self.url = url
        self.status = status
        self.method = method
        self.msg = msg

    def __str__(self):
        return f"IncidentAPIException: status={self.status} url={self.url} method={self.method}"


TIMEOUT = 5
DEFAULT_INCIDENT_SEVERITY = "Pending"
DEFAULT_INCIDENT_STATUS = "active"
DEFAULT_ACTIVITY_KIND = "userNote"


class IncidentAPIClient:
    INCIDENT_BASE_PATH = f"/api/plugins/{PluginID.INCIDENT}/resources/"

    def __init__(self, api_url: str, api_token: str) -> None:
        self.api_token = api_token
        self.api_url = urljoin(api_url, self.INCIDENT_BASE_PATH)

    @property
    def _request_headers(self):
        return {"User-Agent": settings.GRAFANA_COM_USER_AGENT, "Authorization": f"Bearer {self.api_token}"}

    def _make_request(self, url, *args, **kwargs):
        try:
            response = requests.post(url, *args, **kwargs)
        except RequestException as e:
            raise IncidentAPIException(
                status=e.response.status_code if e.response else 500,
                url=e.response.request.url if e.response else url,
                msg=e.response.text if e.response else "Unexpected error",
                method=e.response.request.method if e.response else "POST",
            )
        return response

    def _check_response(self, response: requests.models.Response):
        message = ""

        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("error", response.reason)
            except JSONDecodeError:
                message = response.reason

            raise IncidentAPIException(
                status=response.status_code,
                url=response.request.url,
                msg=message,
                method=response.request.method,
            )

    def create_incident(
        self,
        title: str,
        severity: str = DEFAULT_INCIDENT_SEVERITY,
        status: str = DEFAULT_INCIDENT_STATUS,
        attachCaption: str = "",
        attachURL: str = "",
    ) -> typing.Tuple[IncidentDetails, requests.models.Response]:
        endpoint = "api/v1/IncidentsService.CreateIncident"
        url = self.api_url + endpoint
        # NOTE: invalid severity will raise a 500 error
        response = self._make_request(
            url,
            json={
                "title": title,
                "severity": severity,
                "attachCaption": attachCaption,
                "attachURL": attachURL,
                "status": status,
            },
            timeout=TIMEOUT,
            headers=self._request_headers,
        )
        self._check_response(response)
        return response.json().get("incident"), response

    def get_incident(self, incident_id: str) -> typing.Tuple[IncidentDetails, requests.models.Response]:
        endpoint = "api/v1/IncidentsService.GetIncident"
        url = self.api_url + endpoint
        response = self._make_request(
            url, json={"incidentID": incident_id}, timeout=TIMEOUT, headers=self._request_headers
        )
        self._check_response(response)
        return response.json().get("incident"), response

    def get_severities(self) -> typing.Tuple[typing.List[SeverityDetails], requests.models.Response]:
        # NOTE: internal endpoint
        endpoint = "api/SeveritiesService.GetOrgSeverities"
        url = self.api_url + endpoint
        # pass empty json payload otherwise it will return a 500 response
        response = self._make_request(url, timeout=TIMEOUT, headers=self._request_headers, json={})
        self._check_response(response)
        return response.json().get("severities"), response

    def add_activity(
        self, incident_id: str, body: str, kind: str = DEFAULT_ACTIVITY_KIND
    ) -> typing.Tuple[ActivityItemDetails, requests.models.Response]:
        endpoint = "api/v1/ActivityService.AddActivity"
        url = self.api_url + endpoint
        response = self._make_request(
            url,
            json={"incidentID": incident_id, "activityKind": kind, "body": body},
            timeout=TIMEOUT,
            headers=self._request_headers,
        )
        self._check_response(response)
        return response.json().get("activityItem"), response
