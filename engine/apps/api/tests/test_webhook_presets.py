import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset_options import WebhookPresetOptions

TEST_WEBHOOK_PRESET_FACTORY_NAME = "test webhook preset instance"
TEST_WEBHOOK_PRESET_NAME = "Test Webhook"
TEST_WEBHOOK_PRESET_ID = "test_webhook"
TEST_WEBHOOK_LOGO = "test_logo"
TEST_WEBHOOK_PRESET_DESCRIPTION = "Description of test webhook preset"
TEST_WEBHOOK_PRESET_IGNORED_FIELDS = ["url", "http_method"]


def webhook_preset_override(instance: Webhook, created: bool):
    instance.name = TEST_WEBHOOK_PRESET_FACTORY_NAME
    instance.data = instance.organization.org_title


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
