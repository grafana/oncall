import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel


@pytest.mark.django_db
def test_integration_json_data_too_big(settings, make_organization, make_user, make_alert_receive_channel):
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 50

    organization = make_organization()
    user = make_user(organization=organization)
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
def test_integration_form_data_too_big(settings, make_organization, make_user, make_alert_receive_channel):
    settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 50

    organization = make_organization()
    user = make_user(organization=organization)
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
