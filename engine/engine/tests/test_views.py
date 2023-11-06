import sys
from importlib import import_module, reload
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import clear_url_caches
from rest_framework import status
from rest_framework.test import APIClient


def reload_urlconf():
    clear_url_caches()
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])
    return import_module(settings.ROOT_URLCONF)


@pytest.mark.parametrize(
    "detached_integrations,urlconf,is_cache_updated",
    [
        (False, None, True),
        (True, None, False),
        (True, "engine.integrations_urls", True),
    ],
)
def test_startupprobe_populates_integrations_cache(settings, detached_integrations, urlconf, is_cache_updated):
    settings.DETACHED_INTEGRATIONS_SERVER = detached_integrations
    if urlconf:
        settings.ROOT_URLCONF = urlconf
    reload_urlconf()

    client = APIClient()

    with patch(
        "apps.integrations.mixins.AlertChannelDefiningMixin.update_alert_receive_channel_cache"
    ) as mock_update_cache:
        response = client.get("/startupprobe/")

    assert response.status_code == status.HTTP_200_OK
    assert mock_update_cache.called == is_cache_updated
