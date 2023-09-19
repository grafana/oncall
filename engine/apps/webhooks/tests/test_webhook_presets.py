import pytest

from apps.webhooks.models import Webhook
from conftest import TEST_WEBHOOK_PRESET_ID, TEST_WEBHOOK_PRESET_URL


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
