import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.views.features import Feature


@pytest.mark.django_db
def test_features_view(
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
@pytest.mark.parametrize(
    "feature_attr,expected_feature",
    [
        ("FEATURE_SLACK_INTEGRATION_ENABLED", Feature.SLACK),
        ("FEATURE_TELEGRAM_INTEGRATION_ENABLED", Feature.TELEGRAM),
        ("FEATURE_LIVE_SETTINGS_ENABLED", Feature.LIVE_SETTINGS),
    ],
)
def test_core_features_switch(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    feature_attr,
    expected_feature,
):
    _, user, token = make_organization_and_user_with_plugin_token()
    setattr(settings, feature_attr, True)

    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert expected_feature in response.json()

    setattr(settings, feature_attr, False)
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert expected_feature not in response.json()


@pytest.mark.django_db
@override_settings(GRAFANA_CLOUD_NOTIFICATIONS_ENABLED=True)
def test_oss_features_enabled_in_oss_installation_by_default(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert Feature.GRAFANA_CLOUD_CONNECTION in response.json()
    assert Feature.GRAFANA_CLOUD_NOTIFICATIONS in response.json()
    assert Feature.MSTEAMS not in response.json()


@pytest.mark.django_db
@override_settings(IS_OPEN_SOURCE=False)
def test_non_oss_features_enabled(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert Feature.MSTEAMS in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "feature_attr,expected_feature",
    [
        ("GRAFANA_CLOUD_NOTIFICATIONS_ENABLED", Feature.GRAFANA_CLOUD_NOTIFICATIONS),
    ],
)
def test_oss_features_switch(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    feature_attr,
    expected_feature,
):
    _, user, token = make_organization_and_user_with_plugin_token()
    setattr(settings, feature_attr, True)

    client = APIClient()
    url = reverse("api-internal:features")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert expected_feature in response.json()

    setattr(settings, feature_attr, False)
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert expected_feature not in response.json()
