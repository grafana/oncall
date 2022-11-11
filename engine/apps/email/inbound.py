import logging

from anymail.inbound import AnymailInboundMessage
from anymail.signals import AnymailInboundEvent
from anymail.webhooks import amazon_ses, mailgun, mailjet, mandrill, postal, postmark, sendgrid, sparkpost
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.utils import live_settings
from apps.integrations.mixins import AlertChannelDefiningMixin
from apps.integrations.tasks import create_alert

logger = logging.getLogger(__name__)


# {<ESP name>: (<django-anymail inbound webhook view class>, <webhook secret argument name to pass to the view>), ...}
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
    assert (
        live_settings.INBOUND_EMAIL_ESP in INBOUND_EMAIL_ESP_OPTIONS.keys()
    ), f"INBOUND_EMAIL_ESP env variable must be on of the following: {INBOUND_EMAIL_ESP_OPTIONS.keys()}"
    assert live_settings.INBOUND_EMAIL_WEBHOOK_SECRET, "INBOUND_EMAIL_WEBHOOK_SECRET env variable must be set"

    view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[live_settings.INBOUND_EMAIL_ESP]

    kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
    view = view_class(**kwargs)

    view.run_validators(request)
    events = view.parse_events(request)

    return [event.message for event in events if isinstance(event, AnymailInboundEvent)]


class InboundEmailWebhookView(AlertChannelDefiningMixin, APIView):
    def dispatch(self, request, *args, **kwargs):
        if not live_settings.INBOUND_EMAIL_ESP or not live_settings.INBOUND_EMAIL_DOMAIN:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Some ESPs verify the webhook with a HEAD request at configuration time
        if request.method.lower() == "head":
            return Response(status=status.HTTP_200_OK)

        message = get_messages_from_esp_request(request)[0]

        token_to = message.to[0].address.split("@")[0]
        token_recipient = message.envelope_recipient.split("@")[0]

        result = self.try_dispatch_with_token(token_to, request, args, kwargs)
        if result:
            return result

        result = self.try_dispatch_with_token(token_recipient, request, args, kwargs)
        if result:
            return result

        raise PermissionDenied("Integration key was not found. Permission denied.")

    def try_dispatch_with_token(self, token, request, args, kwargs):
        try:
            kwargs["alert_channel_key"] = token
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            logger.info(f"Permission denied for token: {token}")
            kwargs.pop("alert_channel_key")
            return None

    def post(self, request, alert_receive_channel):
        messages = get_messages_from_esp_request(request)

        for message in messages:
            title = message.subject
            message = message.text.strip()

            payload = {"title": title, "message": message}

            create_alert.delay(
                title=title,
                message=message,
                alert_receive_channel=alert_receive_channel.pk,
                image_url=None,
                link_to_upstream_details=payload.get("link_to_upstream_details"),
                integration_unique_data=payload,
                raw_request_data=request.data,
            )

        return Response("OK", status=status.HTTP_200_OK)
