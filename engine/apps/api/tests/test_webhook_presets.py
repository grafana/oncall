import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook
from apps.webhooks.models.webhook import WEBHOOK_FIELD_PLACEHOLDER
from apps.webhooks.presets.preset_options import WebhookPresetOptions

TEST_WEBHOOK_PRESET_URL = "https://test123.com"
TEST_WEBHOOK_PRESET_NAME = "Test Webhook"
TEST_WEBHOOK_PRESET_ID = "test_webhook"
TEST_WEBHOOK_LOGO = "test_logo"
TEST_WEBHOOK_PRESET_DESCRIPTION = "Description of test webhook preset"
TEST_WEBHOOK_PRESET_IGNORED_FIELDS = ["url", "http_method"]


def webhook_preset_override(instance: Webhook):
    instance.data = instance.organization.org_title
    instance.url = TEST_WEBHOOK_PRESET_URL
    instance.http_method = "GET"


@pytest.fixture()
def webhook_preset_api_setup(make_organization_and_user_with_plugin_token, make_custom_webhook):
    organization, user, token = make_organization_and_user_with_plugin_token()
    WebhookPresetOptions.WEBHOOK_PRESET_CHOICES = [
        {
            "id": TEST_WEBHOOK_PRESET_ID,
            "name": TEST_WEBHOOK_PRESET_NAME,
            "logo": TEST_WEBHOOK_LOGO,
            "description": TEST_WEBHOOK_PRESET_DESCRIPTION,
            "ignored_fields": TEST_WEBHOOK_PRESET_IGNORED_FIELDS,
        }
    ]
    WebhookPresetOptions.WEBHOOK_PRESET_OVERRIDE[TEST_WEBHOOK_PRESET_ID] = webhook_preset_override
    WebhookPresetOptions.WEBHOOK_PRESET_METADATA[TEST_WEBHOOK_PRESET_ID] = WebhookPresetOptions.WEBHOOK_PRESET_CHOICES[
        0
    ]
    return user, token, organization


@pytest.mark.django_db
def test_get_webhook_preset_options(webhook_preset_api_setup, make_user_auth_headers):
    user, token, organization = webhook_preset_api_setup
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
def test_create_webhook_from_preset(webhook_preset_api_setup, make_user_auth_headers):
    user, token, organization = webhook_preset_api_setup
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
        "trigger_type_name": "Alert Group Created",
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response
    assert webhook.password == data["password"]
    assert webhook.authorization_header == data["authorization_header"]
