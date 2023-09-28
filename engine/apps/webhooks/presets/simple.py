from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset import WebhookPreset, WebhookPresetMetadata


class SimpleWebhookPreset(WebhookPreset):
    def _metadata(self) -> WebhookPresetMetadata:
        return WebhookPresetMetadata(
            id="simple_webhook",
            name="Simple",
            logo="webhook",
            description="A simple webhook which sends the alert group data to a given URL. Triggered as an escalation step.",
            controlled_fields=[
                "trigger_type",
                "http_method",
                "integration_filter",
                "headers",
                "username",
                "password",
                "authorization_header",
                "trigger_template",
                "forward_all",
                "data",
            ],
        )

    def override_parameters_before_save(self, webhook: Webhook):
        webhook.http_method = "POST"
        webhook.trigger_type = Webhook.TRIGGER_ESCALATION_STEP
        webhook.forward_all = True

    def override_parameters_at_runtime(self, webhook: Webhook):
        pass
