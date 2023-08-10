from unittest import mock

import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from apps.alerts.models import AlertReceiveChannel


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

    response = c.post(url, data={"message": "This is the test alert from amixr"})
    assert response.status_code == 200
    response = c.post(url, data={"message": "This is the test alert from amixr"})
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
