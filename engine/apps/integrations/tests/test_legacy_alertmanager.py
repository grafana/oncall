from unittest import mock

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel


@mock.patch("apps.integrations.tasks.create_alertmanager_alerts.apply_async", return_value=None)
@mock.patch("apps.integrations.tasks.create_alert.apply_async", return_value=None)
@pytest.mark.django_db
def test_legacy_am_integrations(
    mocked_create_alert, mocked_create_am_alert, make_organization_and_user, make_alert_receive_channel
):
    organization, user = make_organization_and_user()

    alertmanager = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )
    legacy_alertmanager = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
    )

    data = {
        "alerts": [
            {
                "endsAt": "0001-01-01T00:00:00Z",
                "labels": {
                    "job": "node",
                    "group": "production",
                    "instance": "localhost:8081",
                    "severity": "critical",
                    "alertname": "InstanceDown",
                },
                "status": "firing",
                "startsAt": "2023-06-12T08:24:38.326Z",
                "annotations": {
                    "title": "Instance localhost:8081 down",
                    "description": "localhost:8081 of job node has been down for more than 1 minute.",
                },
                "fingerprint": "f404ecabc8dd5cd7",
                "generatorURL": "",
            },
            {
                "endsAt": "0001-01-01T00:00:00Z",
                "labels": {
                    "job": "node",
                    "group": "canary",
                    "instance": "localhost:8082",
                    "severity": "critical",
                    "alertname": "InstanceDown",
                },
                "status": "firing",
                "startsAt": "2023-06-12T08:24:38.326Z",
                "annotations": {
                    "title": "Instance localhost:8082 down",
                    "description": "localhost:8082 of job node has been down for more than 1 minute.",
                },
                "fingerprint": "f8f08d4e32c61a9d",
                "generatorURL": "",
            },
            {
                "endsAt": "0001-01-01T00:00:00Z",
                "labels": {
                    "job": "node",
                    "group": "production",
                    "instance": "localhost:8083",
                    "severity": "critical",
                    "alertname": "InstanceDown",
                },
                "status": "firing",
                "startsAt": "2023-06-12T08:24:38.326Z",
                "annotations": {
                    "title": "Instance localhost:8083 down",
                    "description": "localhost:8083 of job node has been down for more than 1 minute.",
                },
                "fingerprint": "39f38c0611ee7abd",
                "generatorURL": "",
            },
        ],
        "status": "firing",
        "version": "4",
        "groupKey": '{}:{alertname="InstanceDown"}',
        "receiver": "combo",
        "numFiring": 3,
        "externalURL": "",
        "groupLabels": {"alertname": "InstanceDown"},
        "numResolved": 0,
        "commonLabels": {"job": "node", "severity": "critical", "alertname": "InstanceDown"},
        "truncatedAlerts": 0,
        "commonAnnotations": {},
    }

    client = APIClient()
    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": alertmanager.token})
    client.post(url, data=data, format="json")
    assert mocked_create_alert.call_count == 1

    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": legacy_alertmanager.token})
    client.post(url, data=data, format="json")
    assert mocked_create_am_alert.call_count == 3
