from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.urls("engine.integrations_urls")
def test_detached_integrations_startupprobe_populates_integrations_cache():
    client = APIClient()

    with patch(
        "apps.integrations.mixins.AlertChannelDefiningMixin.update_alert_receive_channel_fallback_cache"
    ) as mock_update_cache:
        response = client.get("/startupprobe/")

    assert response.status_code == status.HTTP_200_OK
    mock_update_cache.assert_called_once()


def test_startupprobe_populates_integrations_cache():
    client = APIClient()

    with patch(
        "apps.integrations.mixins.AlertChannelDefiningMixin.update_alert_receive_channel_fallback_cache"
    ) as mock_update_cache:
        response = client.get("/startupprobe/")

    assert response.status_code == status.HTTP_200_OK
    mock_update_cache.assert_called_once()
