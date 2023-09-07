from apps.webhooks.models import Webhook

id = "custom_webhook"
title = "Custom Webhook"


def create_webhook(organization):
    webhook = Webhook()
    webhook.http_method = "POST"
    webhook.trigger_type = Webhook.TRIGGER_ESCALATION_STEP
    return webhook


def validate(organization, webhook):
    pass


def post_process(organization, webhook):
    pass
