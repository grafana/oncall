from unittest.mock import call, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel


@pytest.mark.django_db
def test_integration_json_data_too_big(settings, make_organization_and_user, make_alert_receive_channel):
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 50

    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )

    client = APIClient()
    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {"value": "a" * settings.DATA_UPLOAD_MAX_MEMORY_SIZE}
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_integration_form_data_too_big(settings, make_organization_and_user, make_alert_receive_channel):
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 50

    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    )

    client = APIClient()
    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {"value": "a" * settings.DATA_UPLOAD_MAX_MEMORY_SIZE}
    response = client.post(url, data, content_type="application/x-www-form-urlencoded")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.integrations.views.create_alert")
@pytest.mark.parametrize(
    "integration_type",
    [
        arc_type
        for arc_type in AlertReceiveChannel.INTEGRATION_TYPES
        if arc_type not in ["amazon_sns", "grafana", "alertmanager", "grafana_alerting", "maintenance"]
    ],
)
@pytest.mark.django_db
def test_integration_universal_endpoint(
    mock_create_alert, make_organization_and_user, make_alert_receive_channel, integration_type
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": integration_type, "alert_channel_key": alert_receive_channel.token},
    )

    data = {"foo": "bar"}
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    mock_create_alert.apply_async.assert_called_once_with(
        [],
        {
            "title": None,
            "message": None,
            "image_url": None,
            "link_to_upstream_details": None,
            "alert_receive_channel_pk": alert_receive_channel.pk,
            "integration_unique_data": None,
            "raw_request_data": data,
        },
    )


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_wrong_endpoint(
    mock_create_alertmanager_alerts, make_organization_and_user, make_alert_receive_channel
):
    integration_type = "grafana_alerting"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    response = client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    mock_create_alertmanager_alerts.assert_not_called()


@patch("apps.integrations.views.create_alertmanager_alerts")
@pytest.mark.django_db
def test_integration_grafana_endpoint_has_alerts(
    mock_create_alertmanager_alerts, settings, make_organization_and_user, make_alert_receive_channel
):
    settings.DEBUG = False

    integration_type = "grafana"
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        author=user,
        integration=integration_type,
    )

    client = APIClient()
    url = reverse("integrations:grafana", kwargs={"alert_channel_key": alert_receive_channel.token})

    data = {
        "alerts": [
            {
                "foo": 123,
            },
            {
                "foo": 456,
            },
        ]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK

    mock_create_alertmanager_alerts.apply_async.assert_has_calls(
        [
            call((alert_receive_channel.pk, data["alerts"][0])),
            call((alert_receive_channel.pk, data["alerts"][1])),
        ]
    )
