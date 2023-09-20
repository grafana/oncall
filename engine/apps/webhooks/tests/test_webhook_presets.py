import pytest

from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset import WebhookPreset, WebhookPresetMetadata

TEST_WEBHOOK_PRESET_URL = "https://test123.com"
TEST_WEBHOOK_PRESET_NAME = "Test Webhook"
TEST_WEBHOOK_PRESET_ID = "test_webhook"
TEST_WEBHOOK_LOGO = "test_logo"
TEST_WEBHOOK_PRESET_DESCRIPTION = "Description of test webhook preset"
TEST_WEBHOOK_PRESET_IGNORED_FIELDS = ["url", "http_method", "data"]


class TestWebhookPreset(WebhookPreset):
    def _metadata(self) -> WebhookPresetMetadata:
        return WebhookPresetMetadata(
            id=TEST_WEBHOOK_PRESET_ID,
            name=TEST_WEBHOOK_PRESET_NAME,
            logo=TEST_WEBHOOK_LOGO,
            description=TEST_WEBHOOK_PRESET_DESCRIPTION,
            controlled_fields=TEST_WEBHOOK_PRESET_IGNORED_FIELDS,
        )

    def override_parameters_before_save(self, webhook: Webhook):
        webhook.data = webhook.organization.org_title
        webhook.url = TEST_WEBHOOK_PRESET_URL
        webhook.http_method = "GET"

    def override_parameters_at_runtime(self, webhook: Webhook):
        pass


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
