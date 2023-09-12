from apps.webhooks.models import Webhook

metadata = {
    "id": "simple_webhook",
    "name": "Simple",
    "description": "A simple webhook which POSTs the alert group data to a given URL.  Triggered as an escalation step and hiding advanced webhook parameters",
    "ignored_fields": [
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
}


def override_webhook_parameters(instance: Webhook):
    instance.http_method = "POST"
    instance.trigger_type = Webhook.TRIGGER_ESCALATION_STEP
    instance.forward_all = True
