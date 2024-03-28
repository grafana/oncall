from unittest.mock import PropertyMock, patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_integration_backsync_endpoint(
    make_organization,
    make_alert_receive_channel,
    make_token_for_integration,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    _, token = make_token_for_integration(alert_receive_channel, organization)

    client = APIClient()
    url = reverse("integrations:integration_backsync")

    response = client.post(url, format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_integration_backsync_endpoint_wrong_token(
    make_organization,
    make_alert_receive_channel,
):
    client = APIClient()
    url = reverse("integrations:integration_backsync")
    response = client.post(url, format="json", HTTP_AUTHORIZATION="randomtesttoken")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_integration_backsync_endpoint_throttling(
    make_organization,
    make_alert_receive_channel,
    make_token_for_integration,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    _, token = make_token_for_integration(alert_receive_channel, organization)

    client = APIClient()
    url = reverse("integrations:integration_backsync")
    cache.clear()

    with patch(
        "apps.integrations.throttlers.integration_backsync_throttler.BacksyncRateThrottle.rate",
        new_callable=PropertyMock,
    ) as mocked_rate:
        mocked_rate.return_value = "1/m"

        response = client.post(url, format="json", HTTP_AUTHORIZATION=token)
        assert response.status_code == status.HTTP_200_OK

        response = client.post(url, format="json", HTTP_AUTHORIZATION=f"{token}")
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
