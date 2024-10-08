from unittest import mock

import pytest
from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse
from rest_framework import status

from apps.alerts.models import AlertReceiveChannel
from apps.integrations.mixins import IntegrationRateLimitMixin
from apps.integrations.mixins.ratelimit_mixin import RATELIMIT_INTEGRATION
from common.api_helpers.custom_ratelimit import load_custom_ratelimits


@pytest.fixture(autouse=True)
def clear_cache():
    # Ratelimit keys are stored in cache. Clean it before and after every test to make them idempotent.
    cache.clear()


@mock.patch("ratelimit.utils._split_rate", return_value=(1, 60))
@mock.patch("apps.integrations.tasks.create_alert.apply_async", return_value=None)
@pytest.mark.django_db
def test_ratelimit_alerts_per_integration(
    mocked_task,
    mocked_rate,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    integration = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK)
    url = reverse(
        "integrations:universal",
        kwargs={"integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK, "alert_channel_key": integration.token},
    )

    c = Client()

    response = c.post(url, data={"message": "This is the test alert"})
    assert response.status_code == 200
    response = c.post(url, data={"message": "This is the test alert"})
    assert response.status_code == 429

    assert mocked_task.call_count == 1


@mock.patch("ratelimit.utils._split_rate", return_value=(1, 60))
@mock.patch("apps.integrations.tasks.create_alert.apply_async", return_value=None)
@pytest.mark.django_db
def test_ratelimit_alerts_per_team(
    mocked_task,
    mocked_rate,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    integration_1 = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK)
    url_1 = reverse(
        "integrations:universal",
        kwargs={"integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK, "alert_channel_key": integration_1.token},
    )
    integration_2 = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK)

    url_2 = reverse(
        "integrations:universal",
        kwargs={"integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK, "alert_channel_key": integration_2.token},
    )

    c = Client()

    response = c.post(url_1, data={"message": "This is the test alert from amixr"})
    assert response.status_code == 200

    response = c.post(url_2, data={"message": "This is the test alert from amixr"})
    assert response.status_code == 429

    assert mocked_task.call_count == 1


@mock.patch("ratelimit.utils._split_rate", return_value=(1, 60))
@mock.patch("apps.heartbeat.tasks.process_heartbeat_task.apply_async", return_value=None)
@pytest.mark.django_db
def test_ratelimit_integration_heartbeats(
    mocked_task,
    mocked_rate,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    integration = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK)
    url = reverse("integrations:webhook_heartbeat", kwargs={"alert_channel_key": integration.token})

    c = Client()

    response = c.post(url)
    assert response.status_code == 200

    response = c.post(url)
    assert response.status_code == 429

    response = c.get(url)
    assert response.status_code == 429


# mocking rate limits to 1/m per integration and 3/m per organization
@mock.patch("ratelimit.utils._split_rate", new=lambda rate: (1, 60) if rate == RATELIMIT_INTEGRATION else (3, 60))
@pytest.mark.django_db
def test_ratelimit_integration_and_organization(
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()

    integrations = [
        make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK) for _ in range(4)
    ]
    urls = [
        reverse(
            "integrations:universal",
            kwargs={
                "integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK,
                "alert_channel_key": integration.token,
            },
        )
        for integration in integrations
    ]

    client = Client()

    response = client.post(urls[0])
    assert response.status_code == status.HTTP_200_OK

    response = client.post(urls[0])
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.content.decode() == IntegrationRateLimitMixin.TEXT_INTEGRATION.format(
        integration=integrations[0].verbal_name
    )

    response = client.post(urls[1])
    assert response.status_code == status.HTTP_200_OK

    response = client.post(urls[1])
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.content.decode() == IntegrationRateLimitMixin.TEXT_INTEGRATION.format(
        integration=integrations[1].verbal_name
    )

    response = client.post(urls[2])
    assert response.status_code == status.HTTP_200_OK

    response = client.post(urls[3])
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.content.decode() == IntegrationRateLimitMixin.TEXT_WORKSPACE


@pytest.mark.django_db
def test_custom_throttling(make_organization, make_alert_receive_channel):
    organization_with_custom_ratelimit = make_organization()
    integration_with_custom_ratelimit = make_alert_receive_channel(
        organization_with_custom_ratelimit, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK
    )
    url_with_custom_ratelimit = reverse(
        "integrations:universal",
        kwargs={
            "integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK,
            "alert_channel_key": integration_with_custom_ratelimit.token,
        },
    )

    integration_with_custom_ratelimit_2 = make_alert_receive_channel(
        organization_with_custom_ratelimit, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK
    )
    url_with_custom_ratelimit_2 = reverse(
        "integrations:universal",
        kwargs={
            "integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK,
            "alert_channel_key": integration_with_custom_ratelimit_2.token,
        },
    )

    organization_with_default_ratelimit = make_organization()
    integration_with_default_ratelimit = make_alert_receive_channel(
        organization_with_default_ratelimit, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK
    )
    url_with_default_ratelimit = reverse(
        "integrations:universal",
        kwargs={
            "integration_type": AlertReceiveChannel.INTEGRATION_WEBHOOK,
            "alert_channel_key": integration_with_default_ratelimit.token,
        },
    )
    cache.clear()

    CUSTOM_RATELIMITS_STR = (
        '{"'
        + str(organization_with_custom_ratelimit.pk)
        + '": {"integration": "2/m","organization": "3/m","public_api": "1/m"}}'
    )

    with override_settings(CUSTOM_RATELIMITS=load_custom_ratelimits(CUSTOM_RATELIMITS_STR)):
        client = Client()

        # Organization without custom ratelimit should use default ratelimit
        for _ in range(5):
            response = client.post(url_with_default_ratelimit)
            assert response.status_code == status.HTTP_200_OK

        # Organization with custom ratelimit will be ratelimited after 2 requests because of integration rate limit
        response = client.post(url_with_custom_ratelimit)

        assert response.status_code == status.HTTP_200_OK

        response = client.post(url_with_custom_ratelimit)

        assert response.status_code == status.HTTP_200_OK

        response = client.post(url_with_custom_ratelimit)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.content.decode() == IntegrationRateLimitMixin.TEXT_INTEGRATION.format(
            integration=integration_with_custom_ratelimit.verbal_name
        )

        # Organization with custom ratelimit will be ratelimited after 3 requests because of organization rate limit
        response = client.post(url_with_custom_ratelimit_2)

        assert response.status_code == status.HTTP_200_OK

        response = client.post(url_with_custom_ratelimit_2)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.content.decode() == IntegrationRateLimitMixin.TEXT_WORKSPACE
