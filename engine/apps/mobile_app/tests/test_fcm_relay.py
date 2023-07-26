import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from firebase_admin.exceptions import FirebaseError
from rest_framework import status
from rest_framework.test import APIClient

from apps.mobile_app.fcm_relay import FCMRelayThrottler, _get_message_from_request_data, fcm_relay_async
from apps.mobile_app.models import FCMDevice
from apps.mobile_app.tasks import _get_alert_group_escalation_fcm_message


@pytest.mark.django_db
def test_fcm_relay_disabled(
    settings,
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


def test_get_message_from_request_data():
    token = "test_token"
    data = {"test_data_key": "test_data_value"}
    apns = {"headers": {"apns-priority": "10"}, "payload": {"aps": {"thread-id": "test_thread_id"}}}
    android = {"priority": "high"}
    message = _get_message_from_request_data(token, data, apns, android)

    assert message.token == "test_token"
    assert message.data == {"test_data_key": "test_data_value"}
    assert message.apns.headers == {"apns-priority": "10"}
    assert message.apns.payload.aps.thread_id == "test_thread_id"
    assert message.android.priority == "high"


@pytest.mark.django_db
def test_fcm_relay_serialize_deserialize(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    device = FCMDevice.objects.create(user=user, registration_id="test_device_id")

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    # Imitate sending a message to the FCM relay endpoint
    original_message = _get_alert_group_escalation_fcm_message(alert_group, user, device, critical=False)
    request_data = json.loads(str(original_message))

    # Imitate receiving a message from the FCM relay endpoint
    relayed_message = _get_message_from_request_data(
        request_data["token"], request_data["data"], request_data["apns"], request_data["android"]
    )

    # Check that the message is the same after serialization and deserialization
    assert json.loads(str(original_message)) == json.loads(str(relayed_message))
