import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.views.features import (
    FEATURE_GRAFANA_CLOUD_CONNECTION,
    FEATURE_LIVE_SETTINGS,
    FEATURE_SLACK,
    FEATURE_TELEGRAM,
)


@pytest.mark.django_db
def test_features(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    """
    Test access to features without credentials
    """
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_select_features_all_enabled(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    settings.OSS_INSTALLATION = True
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = True
    settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED = True
    settings.FEATURE_LIVE_SETTINGS_ENABLED = True
    settings.FEATURE_GRAFANA_CLOUD_CONNECTION = True
    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [FEATURE_SLACK, FEATURE_TELEGRAM, FEATURE_GRAFANA_CLOUD_CONNECTION, FEATURE_LIVE_SETTINGS]


@pytest.mark.django_db
def test_select_features_all_disabled(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    settings.OSS_INSTALLATIONs = False
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = False
    settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED = False
    settings.FEATURE_LIVE_SETTINGS_ENABLED = False
    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
