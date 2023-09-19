import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.webhooks.models import Webhook
from conftest import (
    TEST_WEBHOOK_LOGO,
    TEST_WEBHOOK_PRESET_DESCRIPTION,
    TEST_WEBHOOK_PRESET_ID,
    TEST_WEBHOOK_PRESET_IGNORED_FIELDS,
    TEST_WEBHOOK_PRESET_NAME,
    TEST_WEBHOOK_PRESET_URL,
)


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
def test_create_webhook_from_preset(webhook_preset_api_setup, make_user_auth_headers, make_custom_webhook):
    user, token, organization = webhook_preset_api_setup
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )

    webhook.refresh_from_db()
    assert webhook.url == TEST_WEBHOOK_PRESET_URL
    assert webhook.http_method == "GET"
    assert webhook.data == organization.org_title
