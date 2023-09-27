from apps.webhooks.models import Webhook
from apps.webhooks.presets.preset import WebhookPreset, WebhookPresetMetadata


class AdvancedWebhookPreset(WebhookPreset):
    def _metadata(self) -> WebhookPresetMetadata:
        return WebhookPresetMetadata(
            id="advanced_webhook",
            name="Advanced",
            logo="webhook",
            description="An advanced webhook with all available settings and template options.",
            controlled_fields=[],
        )

    def override_parameters_before_save(self, webhook: Webhook):
        pass

    def override_parameters_at_runtime(self, webhook: Webhook):
        pass
