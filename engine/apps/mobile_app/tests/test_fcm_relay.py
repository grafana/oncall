from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.mobile_app.fcm_relay import FCMRelayThrottler


@pytest.mark.django_db
def test_fcm_relay_disabled(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
    settings.FEATURE_MOBILE_APP_INTEGRATION_ENABLED = True
    settings.FCM_RELAY_ENABLED = False

    organization, user, token = make_organization_and_user_with_plugin_token()
    _, token = make_public_api_token(user, organization)

    client = APIClient()
    url = reverse("mobile_app:fcm_relay")

    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_fcm_relay_post(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
    settings.FEATURE_MOBILE_APP_INTEGRATION_ENABLED = True
    settings.FCM_RELAY_ENABLED = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    _, token = make_public_api_token(user, organization)

    client = APIClient()
    url = reverse("mobile_app:fcm_relay")

    data = {
        "token": "test_registration_id",
        "data": {},
        "apns": {},
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_fcm_relay_ratelimit(
    settings,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
    settings.FEATURE_MOBILE_APP_INTEGRATION_ENABLED = True
    settings.FCM_RELAY_ENABLED = True

    organization, user, token = make_organization_and_user_with_plugin_token()
    _, token = make_public_api_token(user, organization)

    client = APIClient()
    url = reverse("mobile_app:fcm_relay")

    data = {
        "token": "test_registration_id",
        "data": {},
        "apns": {},
    }

    with patch.object(FCMRelayThrottler, "rate", "0/m"):
        response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=token)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
