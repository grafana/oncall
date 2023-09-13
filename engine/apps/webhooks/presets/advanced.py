from apps.webhooks.models import Webhook

metadata = {
    "id": "advanced_webhook",
    "name": "Advanced",
    "logo": "webhook",
    "description": "An advanced webhook with all available settings and template options.",
    "ignored_fields": [],
}


def override_webhook_parameters(instance: Webhook):
    pass
