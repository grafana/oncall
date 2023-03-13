import logging

from anymail.exceptions import AnymailWebhookValidationFailure
from anymail.inbound import AnymailInboundMessage
from anymail.signals import AnymailInboundEvent
from anymail.webhooks import amazon_ses, mailgun, mailjet, mandrill, postal, postmark, sendgrid, sparkpost
from django.http import HttpResponse, HttpResponseNotAllowed
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


class InboundEmailWebhookView(AlertChannelDefiningMixin, APIView):
    def dispatch(self, request):
        # http_method_names can't be used due to how AlertChannelDefiningMixin is implemented
        # todo: refactor AlertChannelDefiningMixin
        if not request.method.lower() in ["head", "post"]:
            return HttpResponseNotAllowed(permitted_methods=["head", "post"])

        self._check_inbound_email_settings_set()

        # Some ESPs verify the webhook with a HEAD request at configuration time
        if request.method.lower() == "head":
            return HttpResponse(status=status.HTTP_200_OK)

        messages = get_messages_from_esp_request(request)
        if not messages:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        message = messages[0]
        integration_token = message.to[0].address.split("@")[0]
        return super().dispatch(request, alert_channel_key=integration_token)

    def _check_inbound_email_settings_set(self):
        """
        Checks if INBOUND_EMAIL settings set.
        Returns BadRequest if not.
        """
        # TODO: These settings should be checked before app start.
        if not live_settings.INBOUND_EMAIL_ESP:
            logger.error(f"InboundEmailWebhookView: INBOUND_EMAIL_ESP env variable must be set.")
            return HttpResponse(
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not live_settings.INBOUND_EMAIL_DOMAIN:
            logger.error("InboundEmailWebhookView: INBOUND_EMAIL_DOMAIN env variable must be set.")
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, alert_receive_channel):
        for email in get_messages_from_esp_request(request):
            subject = email.subject
            message = email.text.strip()
            sender = email.from_email.addr_spec

            payload = {"subject": subject, "message": message, "sender": sender}

            create_alert.delay(
                title=subject,
                message=message,
                alert_receive_channel_pk=alert_receive_channel.pk,
                image_url=None,
                link_to_upstream_details=None,
                integration_unique_data=request.data,
                raw_request_data=payload,
            )

        return Response("OK", status=status.HTTP_200_OK)


def get_messages_from_esp_request(request: Request) -> list[AnymailInboundMessage]:
    view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[live_settings.INBOUND_EMAIL_ESP]

    kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
    view = view_class(**kwargs)

    try:
        view.run_validators(request)
        events = view.parse_events(request)
    except AnymailWebhookValidationFailure:
        return []

    return [event.message for event in events if isinstance(event, AnymailInboundEvent)]


def get_integration_token_from_email_message(message: AnymailInboundMessage):
    return message.to[0].address.split("@")[0]
