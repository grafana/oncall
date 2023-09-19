import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook
from apps.webhooks.models.webhook import WEBHOOK_FIELD_PLACEHOLDER
from conftest import (
    TEST_WEBHOOK_LOGO,
    TEST_WEBHOOK_PRESET_DESCRIPTION,
    TEST_WEBHOOK_PRESET_ID,
    TEST_WEBHOOK_PRESET_IGNORED_FIELDS,
    TEST_WEBHOOK_PRESET_NAME,
    TEST_WEBHOOK_PRESET_URL,
)


@pytest.mark.django_db
def test_get_webhook_preset_options(
    make_organization_and_user_with_plugin_token, webhook_preset_api_setup, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:webhooks-preset-options")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["id"] == TEST_WEBHOOK_PRESET_ID
    assert response.data[0]["name"] == TEST_WEBHOOK_PRESET_NAME
    assert response.data[0]["logo"] == TEST_WEBHOOK_LOGO
    assert response.data[0]["description"] == TEST_WEBHOOK_PRESET_DESCRIPTION
    assert response.data[0]["ignored_fields"] == TEST_WEBHOOK_PRESET_IGNORED_FIELDS


@pytest.mark.django_db
def test_create_webhook_from_preset(
    make_organization_and_user_with_plugin_token, webhook_preset_api_setup, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "team": None,
        "password": "secret_password",
        "authorization_header": "auth 1234",
        "preset": TEST_WEBHOOK_PRESET_ID,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    webhook = Webhook.objects.get(public_primary_key=response.data["id"])

    expected_response = data | {
        "id": webhook.public_primary_key,
        "url": TEST_WEBHOOK_PRESET_URL,
        "data": organization.org_title,
        "username": None,
        "password": WEBHOOK_FIELD_PLACEHOLDER,
        "authorization_header": WEBHOOK_FIELD_PLACEHOLDER,
        "forward_all": True,
        "headers": None,
        "http_method": "GET",
        "integration_filter": None,
        "is_webhook_enabled": True,
        "is_legacy": False,
        "last_response_log": {
            "request_data": "",
            "request_headers": "",
            "timestamp": None,
            "content": "",
            "status_code": None,
            "request_trigger": "",
            "url": "",
            "event_data": "",
        },
        "trigger_template": None,
        "trigger_type": str(data["trigger_type"]),
        "trigger_type_name": "Alert Group Created",
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response
    assert webhook.password == data["password"]
    assert webhook.authorization_header == data["authorization_header"]


@pytest.mark.django_db
def test_invalid_create_webhook_with_preset(
    make_organization_and_user_with_plugin_token, webhook_preset_api_setup, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:webhooks-list")

    data = {
        "name": "the_webhook",
        "trigger_type": Webhook.TRIGGER_ALERT_GROUP_CREATED,
        "url": "https://test12345.com",
        "preset": TEST_WEBHOOK_PRESET_ID,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["preset"][0] == "url is controlled by preset, cannot create"


@pytest.mark.django_db
def test_update_webhook_from_preset(
    make_organization_and_user_with_plugin_token, webhook_preset_api_setup, make_user_auth_headers, make_custom_webhook
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )

    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    data = {
        "name": "the_webhook 2",
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == data["name"]

    webhook.refresh_from_db()
    assert webhook.name == data["name"]
    assert webhook.url == TEST_WEBHOOK_PRESET_URL
    assert webhook.http_method == "GET"
    assert webhook.data == organization.org_title


@pytest.mark.django_db
def test_invalid_update_webhook_from_preset(
    make_organization_and_user_with_plugin_token, webhook_preset_api_setup, make_user_auth_headers, make_custom_webhook
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )

    client = APIClient()
    url = reverse("api-internal:webhooks-detail", kwargs={"pk": webhook.public_primary_key})

    data = {
        "preset": "some_other_preset",
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["preset"][0] == "This field once set cannot be modified."

    data = {
        "data": "some_other_data",
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
