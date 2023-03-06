from unittest.mock import patch

import pytest
from django.urls import reverse
from fcm_django.models import FCMDevice
from firebase_admin.exceptions import FirebaseError
from rest_framework import status
from rest_framework.test import APIClient

from apps.mobile_app.fcm_relay import FCMRelayThrottler, fcm_relay_async


@pytest.mark.django_db
def test_fcm_relay_disabled(
    settings,
    load_mobile_app_urls,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
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
    load_mobile_app_urls,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
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
    load_mobile_app_urls,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
):
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


@pytest.mark.django_db
def test_fcm_relay_async_retry():
    # check that FirebaseError is raised when send_message returns it so Celery task can retry
    with patch.object(
        FCMDevice, "send_message", return_value=FirebaseError(code="test_error_code", message="test_error_message")
    ):
        with pytest.raises(FirebaseError):
            fcm_relay_async(token="test_token", data={}, apns={})
