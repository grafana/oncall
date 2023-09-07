import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset_options import WebhookPresetOptions

TEST_WEBHOOK_PRESET_FACTORY_NAME = "test webhook preset instance"
TEST_WEBHOOK_PRESET_NAME = "Test Webhook"
TEST_WEBHOOK_PRESET_ID = "test_webhook"


def webhook_preset_factory(organization):
    webhook = Webhook()
    webhook.name = TEST_WEBHOOK_PRESET_FACTORY_NAME
    webhook.data = organization.org_title
    return webhook


@pytest.fixture()
def webhook_preset_api_setup(make_organization_and_user_with_plugin_token, make_custom_webhook):
    organization, user, token = make_organization_and_user_with_plugin_token()
    WebhookPresetOptions.WEBHOOK_PRESET_CHOICES = ((TEST_WEBHOOK_PRESET_ID, TEST_WEBHOOK_PRESET_NAME),)
    WebhookPresetOptions.WEBHOOK_PRESET_FACTORIES[TEST_WEBHOOK_PRESET_ID] = webhook_preset_factory
    return user, token, organization


@pytest.mark.django_db
def test_get_webhook_preset_options(webhook_preset_api_setup, make_user_auth_headers):
    user, token, organization = webhook_preset_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-preset-options")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["value"] == TEST_WEBHOOK_PRESET_ID
    assert response.data[0]["display_name"] == TEST_WEBHOOK_PRESET_NAME


@pytest.mark.django_db
def test_get_webhook_preset_from_preset(webhook_preset_api_setup, make_user_auth_headers):
    user, token, organization = webhook_preset_api_setup
    client = APIClient()
    url = reverse("api-internal:webhooks-preset")

    response = client.get(f"{url}", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.get(f"{url}?id=nonexistent", format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.get(f"{url}?id={TEST_WEBHOOK_PRESET_ID}", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == TEST_WEBHOOK_PRESET_FACTORY_NAME
    assert response.data["data"] == organization.org_title
