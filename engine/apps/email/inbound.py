from anymail.inbound import AnymailInboundMessage
from anymail.signals import AnymailInboundEvent
from anymail.webhooks import amazon_ses, mailgun, mailjet, mandrill, postal, postmark, sendgrid, sparkpost
from rest_framework.request import Request

from apps.base.utils import live_settings

# {<ESP-NAME>: (<django-anymail inbound webhook view class>, <webhook secret argument name to pass to the view>), ...}
INBOUND_EMAIL_ESP_OPTIONS = {
    "amazon_ses": (amazon_ses.AmazonSESInboundWebhookView, None),
    "mailgun": (mailgun.MailgunInboundWebhookView, "webhook_signing_key"),
    "mailjet": (mailjet.MailjetInboundWebhookView, "webhook_secret"),
    "mandrill": (mandrill.MandrillCombinedWebhookView, "webhook_key"),
    "postal": (postal.PostalInboundWebhookView, "webhook_key"),
    "postmark": (postmark.PostmarkInboundWebhookView, "webhook_secret"),
    "sendgrid": (sendgrid.SendGridInboundWebhookView, "webhook_secret"),
    "sparkpost": (sparkpost.SparkPostInboundWebhookView, "webhook_secret"),
}


def get_messages_from_esp_request(request: Request) -> list[AnymailInboundMessage]:
    assert live_settings.INBOUND_EMAIL_ESP, "INBOUND_EMAIL_ESP env variable must be set"
    assert live_settings.INBOUND_EMAIL_WEBHOOK_SECRET, "INBOUND_EMAIL_WEBHOOK_SECRET env variable must be set"

    view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[live_settings.INBOUND_EMAIL_ESP]

    kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
    view = view_class(**kwargs)

    view.run_validators(request)
    events = view.parse_events(request)

    return [event.message for event in events if isinstance(event, AnymailInboundEvent)]
