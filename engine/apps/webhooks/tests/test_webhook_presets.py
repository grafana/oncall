from unittest.mock import patch

import pytest

from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset import WebhookPreset, WebhookPresetMetadata
from apps.webhooks.tasks.trigger_webhook import make_request
from apps.webhooks.tests.test_trigger_webhook import MockResponse

TEST_WEBHOOK_PRESET_URL = "https://test123.com"
TEST_WEBHOOK_PRESET_NAME = "Test Webhook"
TEST_WEBHOOK_PRESET_ID = "test_webhook"
TEST_WEBHOOK_LOGO = "test_logo"
TEST_WEBHOOK_PRESET_DESCRIPTION = "Description of test webhook preset"
TEST_WEBHOOK_PRESET_CONTROLLED_FIELDS = ["url", "http_method", "data", "authorization_header"]
TEST_WEBHOOK_AUTHORIZATION_HEADER = "Test Auth header 12345"
INVALID_PRESET_ID = "invalid_preset_id"


class TestWebhookPreset(WebhookPreset):
    def _metadata(self) -> WebhookPresetMetadata:
        return WebhookPresetMetadata(
            id=TEST_WEBHOOK_PRESET_ID,
            name=TEST_WEBHOOK_PRESET_NAME,
            logo=TEST_WEBHOOK_LOGO,
            description=TEST_WEBHOOK_PRESET_DESCRIPTION,
            controlled_fields=TEST_WEBHOOK_PRESET_CONTROLLED_FIELDS,
        )

    def override_parameters_before_save(self, webhook: Webhook):
        webhook.data = webhook.organization.org_title
        webhook.url = TEST_WEBHOOK_PRESET_URL
        webhook.http_method = "GET"

    def override_parameters_at_runtime(self, webhook: Webhook):
        webhook.authorization_header = TEST_WEBHOOK_AUTHORIZATION_HEADER


@pytest.mark.django_db
def test_create_webhook_from_preset(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
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
    assert webhook.authorization_header is None


@pytest.mark.django_db
def test_create_webhook_from_invalid_preset(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
    expected = None
    try:
        make_custom_webhook(
            name="the_webhook",
            organization=organization,
            trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
            preset=INVALID_PRESET_ID,
        )
    except NotImplementedError as e:
        expected = e

    assert expected.args[0] == f"Webhook references unknown preset implementation {INVALID_PRESET_ID}"


@pytest.mark.django_db
def test_update_webhook_from_preset(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )

    webhook.refresh_from_db()
    webhook.http_method = "POST"
    webhook.save()

    webhook.refresh_from_db()
    assert webhook.http_method == "GET"


@pytest.mark.django_db
def test_update_webhook_from_invalid_preset(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )
    webhook.refresh_from_db()
    webhook.preset = INVALID_PRESET_ID

    try:
        webhook.save()
    except NotImplementedError as e:
        expected = e

    assert expected.args[0] == f"Webhook references unknown preset implementation {INVALID_PRESET_ID}"

    webhook.refresh_from_db()
    assert webhook.preset == TEST_WEBHOOK_PRESET_ID


@pytest.mark.django_db
def test_webhook_preset_runtime_override(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
        preset=TEST_WEBHOOK_PRESET_ID,
    )

    with patch.object(webhook, "build_url"):
        response = MockResponse()
        with patch.object(webhook, "make_request", return_value=response) as mock_make_request:
            triggered, webhook_status, error, exception = make_request(webhook, None, None)
            assert mock_make_request.call_args.args[1]["headers"]["Authorization"] == TEST_WEBHOOK_AUTHORIZATION_HEADER
            assert triggered
            assert error is None
            assert exception is None

    webhook.refresh_from_db()
    assert webhook.authorization_header is None


@pytest.mark.django_db
def test_webhook_invalid_preset_runtime_override(make_organization, webhook_preset_api_setup, make_custom_webhook):
    organization = make_organization()
    webhook = make_custom_webhook(
        name="the_webhook",
        organization=organization,
        trigger_type=Webhook.TRIGGER_ALERT_GROUP_CREATED,
    )
    webhook.refresh_from_db()

    expected_error = f"Invalid preset {INVALID_PRESET_ID}"
    Webhook.objects.filter(id=webhook.id).update(preset=INVALID_PRESET_ID)
    webhook.refresh_from_db()
    with patch.object(webhook, "build_url"):
        with patch.object(webhook, "make_request") as mock_make_request:
            triggered, webhook_status, error, exception = make_request(webhook, None, None)
            mock_make_request.assert_not_called()
            assert triggered
            assert webhook_status["content"] == expected_error
            assert error == expected_error
            assert exception.args[0] == expected_error

    webhook.refresh_from_db()
    assert webhook.authorization_header is None
