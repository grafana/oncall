import logging
from typing import Optional, TypedDict

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


class EmailAlertPayload(TypedDict):
    subject: str
    message: str
    sender: str


class InboundEmailWebhookView(AlertChannelDefiningMixin, APIView):
    def dispatch(self, request):
        """
        Wrapper to parse integration_token from inbound email address and pass this token to
        AlertChannelDefiningMixin
        """

        # http_method_names can't be used due to how AlertChannelDefiningMixin is implemented
        # todo: refactor AlertChannelDefiningMixin
        if not request.method.lower() in ["head", "post"]:
            return HttpResponseNotAllowed(permitted_methods=["head", "post"])

        self._check_inbound_email_settings_set()

        # Some ESPs verify the webhook with a HEAD request at configuration time
        if request.method.lower() == "head":
            return HttpResponse(status=status.HTTP_200_OK)

        integration_token = self._get_integration_token_from_request(request)
        if integration_token is None:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
        return super().dispatch(request, alert_channel_key=integration_token)

    def post(self, request, alert_receive_channel):
        for message in self._get_messages_from_esp_request(request):
            payload = self._get_alert_payload_from_email_message(message)
            create_alert.delay(
                title=payload["subject"],
                message=payload["message"],
                alert_receive_channel_pk=alert_receive_channel.pk,
                image_url=None,
                link_to_upstream_details=None,
                integration_unique_data=request.data,
                raw_request_data=payload,
            )

        return Response("OK", status=status.HTTP_200_OK)

    def _get_integration_token_from_request(self, request) -> Optional[str]:
        messages = self._get_messages_from_esp_request(request)
        if not messages:
            return None
        return messages[0].to[0].address.split("@")[0]

    def _get_messages_from_esp_request(self, request: Request) -> list[AnymailInboundMessage]:
        view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[live_settings.INBOUND_EMAIL_ESP]

        kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
        view = view_class(**kwargs)

        try:
            view.run_validators(request)
            events = view.parse_events(request)
        except AnymailWebhookValidationFailure:
            return []

        return [event.message for event in events if isinstance(event, AnymailInboundEvent)]

    def _check_inbound_email_settings_set(self):
        """
        Guard method to checks if INBOUND_EMAIL settings present.
        Returns InternalServerError if not.
        """
        # TODO: These settings should be checked before app start.
        if not live_settings.INBOUND_EMAIL_ESP:
            logger.error(f"InboundEmailWebhookView: INBOUND_EMAIL_ESP env variable must be set.")
            return HttpResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not live_settings.INBOUND_EMAIL_DOMAIN:
            logger.error("InboundEmailWebhookView: INBOUND_EMAIL_DOMAIN env variable must be set.")
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_alert_payload_from_email_message(self, email: AnymailInboundMessage) -> EmailAlertPayload:
        subject = email.subject or ""
        subject = subject.strip()
        message = email.text or ""
        message = message.strip()
        sender = email.from_email.addr_spec

        return {"subject": subject, "message": message, "sender": sender}
