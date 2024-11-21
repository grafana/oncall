import logging
from functools import cached_property
from typing import Optional, TypedDict

import requests
from anymail.exceptions import AnymailAPIError, AnymailInvalidAddress, AnymailWebhookValidationFailure
from anymail.inbound import AnymailInboundMessage
from anymail.signals import AnymailInboundEvent
from anymail.webhooks import amazon_ses, mailgun, mailjet, mandrill, postal, postmark, sendgrid, sparkpost
from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.utils import live_settings
from apps.email.validate_amazon_sns_message import validate_amazon_sns_message
from apps.integrations.mixins import AlertChannelDefiningMixin
from apps.integrations.tasks import create_alert

logger = logging.getLogger(__name__)


class AmazonSESValidatedInboundWebhookView(amazon_ses.AmazonSESInboundWebhookView):
    # disable "Your Anymail webhooks are insecure and open to anyone on the web." warning
    warn_if_no_basic_auth = False

    def validate_request(self, request):
        """Add SNS message validation to Amazon SES inbound webhook view, which is not implemented in Anymail."""
        if not validate_amazon_sns_message(self._parse_sns_message(request)):
            raise AnymailWebhookValidationFailure("SNS message validation failed")

    def auto_confirm_sns_subscription(self, sns_message):
        """This method is called after validate_request, so we can be sure that the message is valid."""
        response = requests.get(sns_message["SubscribeURL"])
        response.raise_for_status()


# {<ESP name>: (<django-anymail inbound webhook view class>, <webhook secret argument name to pass to the view>), ...}
INBOUND_EMAIL_ESP_OPTIONS = {
    "amazon_ses": (amazon_ses.AmazonSESInboundWebhookView, None),
    "amazon_ses_validated": (AmazonSESValidatedInboundWebhookView, None),
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
        request.inbound_email_integration_token = integration_token  # used in RequestTimeLoggingMiddleware
        return super().dispatch(request, alert_channel_key=integration_token)

    def post(self, request):
        payload = self.get_alert_payload_from_email_message(self.message)
        create_alert.delay(
            title=payload["subject"],
            message=payload["message"],
            alert_receive_channel_pk=request.alert_receive_channel.pk,
            image_url=None,
            link_to_upstream_details=None,
            integration_unique_data=None,
            raw_request_data=payload,
            received_at=timezone.now().isoformat(),
        )
        return Response("OK", status=status.HTTP_200_OK)

    def get_integration_token_from_request(self, request) -> Optional[str]:
        if not self.message:
            return None
        # First try envelope_recipient field.
        # According to AnymailInboundMessage it's provided not by all ESPs.
        if self.message.envelope_recipient:
            recipients = self.message.envelope_recipient.split(",")
            for recipient in recipients:
                # if there is more than one recipient, the first matching the expected domain will be used
                try:
                    token, domain = recipient.strip().split("@")
                except ValueError:
                    logger.error(
                        f"get_integration_token_from_request: envelope_recipient field has unexpected format: {self.message.envelope_recipient}"
                    )
                    continue
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

    @cached_property
    def message(self) -> AnymailInboundMessage | None:
        esps = live_settings.INBOUND_EMAIL_ESP.split(",")
        for esp in esps:
            view_class, secret_name = INBOUND_EMAIL_ESP_OPTIONS[esp]

            kwargs = {secret_name: live_settings.INBOUND_EMAIL_WEBHOOK_SECRET} if secret_name else {}
            view = view_class(**kwargs)

            try:
                view.run_validators(self.request)
                events = view.parse_events(self.request)
            except (AnymailWebhookValidationFailure, AnymailAPIError):
                continue

            messages = [event.message for event in events if isinstance(event, AnymailInboundEvent)]
            if messages:
                logger.info(f"Received inbound email message from ESP: {esp}")
                return messages[0]

        logger.error("Failed to parse inbound email message")
        return None

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
        sender = self.get_sender_from_email_message(email)

        return {"subject": subject, "message": message, "sender": sender}

    def get_sender_from_email_message(self, email: AnymailInboundMessage) -> str:
        try:
            if isinstance(email.from_email, list):
                sender = email.from_email[0].addr_spec
            else:
                sender = email.from_email.addr_spec
        except AnymailInvalidAddress as e:
            # wasn't able to parse email address from message, return raw value from "From" header
            logger.warning(
                f"get_sender_from_email_message: issue during parsing sender from email message, getting raw value "
                f"instead. Exception: {e}"
            )
            sender = ", ".join(email.get_all("From"))
        return sender
