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

        self.check_inbound_email_settings_set()

        # Some ESPs verify the webhook with a HEAD request at configuration time
        if request.method.lower() == "head":
            return HttpResponse(status=status.HTTP_200_OK)

        integration_token = self.get_integration_token_from_request(request)
        if integration_token is None:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
        return super().dispatch(request, alert_channel_key=integration_token)

    def post(self, request):
        for message in self.get_messages_from_esp_request(request):
            payload = self.get_alert_payload_from_email_message(message)
            create_alert.delay(
                title=payload["subject"],
                message=payload["message"],
                alert_receive_channel_pk=request.alert_receive_channel.pk,
                image_url=None,
                link_to_upstream_details=None,
                integration_unique_data=None,
                raw_request_data=payload,
            )

        return Response("OK", status=status.HTTP_200_OK)

    def get_integration_token_from_request(self, request) -> Optional[str]:
        messages = self.get_messages_from_esp_request(request)
        if not messages:
            return None
        message = messages[0]
        # First try envelope_recipient field.
        # According to AnymailInboundMessage it's provided not by all ESPs.
        if message.envelope_recipient:
            token, domain = message.envelope_recipient.split("@")
            if domain == live_settings.INBOUND_EMAIL_DOMAIN:
                return token
        else:
            logger.info("get_integration_token_from_request: message.envelope_recipient is not present")
        """
        TODO: handle case when envelope_recipient is not provided.
        Now we can't just compare to/cc domains one by one with INBOUND_EMAIL_DOMAIN
        because this check will not work in case of OrganizationMovedException
        """
        # for to in message.to:
        #     if to.domain == live_settings.INBOUND_EMAIL_DOMAIN:
        #         return to.address.split("@")[0]
        # for cc in message.cc:
        #     if cc.domain == live_settings.INBOUND_EMAIL_DOMAIN:
        #         return cc.address.split("@")[0]
        return None

    def get_messages_from_esp_request(self, request: Request) -> list[AnymailInboundMessage]:
        view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[live_settings.INBOUND_EMAIL_ESP]

        kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
        view = view_class(**kwargs)

        try:
            view.run_validators(request)
            events = view.parse_events(request)
        except AnymailWebhookValidationFailure as e:
            logger.info(f"get_messages_from_esp_request: inbound email webhook validation failed: {e}")
            return []

        return [event.message for event in events if isinstance(event, AnymailInboundEvent)]

    def check_inbound_email_settings_set(self):
        """
        Guard method to checks if INBOUND_EMAIL settings present.
        Returns InternalServerError if not.
        """
        # TODO: These settings should be checked before app start.
        if not live_settings.INBOUND_EMAIL_ESP:
            logger.error("InboundEmailWebhookView: INBOUND_EMAIL_ESP env variable must be set.")
            return HttpResponse(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not live_settings.INBOUND_EMAIL_DOMAIN:
            logger.error("InboundEmailWebhookView: INBOUND_EMAIL_DOMAIN env variable must be set.")
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_alert_payload_from_email_message(self, email: AnymailInboundMessage) -> EmailAlertPayload:
        subject = email.subject or ""
        subject = subject.strip()
        message = email.text or ""
        message = message.strip()
        sender = email.from_email.addr_spec

        return {"subject": subject, "message": message, "sender": sender}
