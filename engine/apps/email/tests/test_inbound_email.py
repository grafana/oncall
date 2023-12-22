import json

import pytest
from anymail.inbound import AnymailInboundMessage
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.email.inbound import InboundEmailWebhookView


@pytest.mark.django_db
def test_amazon_ses_provider_load(settings, make_organization_and_user_with_token, make_alert_receive_channel):
    settings.INBOUND_EMAIL_ESP = "amazon_ses"
    settings.INBOUND_EMAIL_DOMAIN = "example.com"

    dummy_channel_token = "dummy-channel-token"

    organization, _, token = make_organization_and_user_with_token()
    _ = make_alert_receive_channel(organization, token=dummy_channel_token)

    recipient = f"{dummy_channel_token}@example.com"
    mime = f"""From: sender@example.com
    Subject: Dummy email message
    To: {recipient}
    Content-Type: text/plain

    Hello!
    """

    message = {
        "notificationType": "Received",
        "receipt": {"action": {"type": "SNS"}, "recipients": [recipient]},
        "content": mime,
    }

    dummy_sns_message_id = "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324"
    dummy_sns_payload = {
        "Type": "Notification",
        "MessageId": dummy_sns_message_id,
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:MyTopic",
        "Subject": "My First Message",
        "Message": json.dumps(message),
    }

    client = APIClient()

    response = client.post(
        reverse("integrations:inbound_email_webhook"),
        data=json.dumps(dummy_sns_payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=token,
        HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        HTTP_X_AMZ_SNS_MESSAGE_ID=dummy_sns_message_id,
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "sender_value,expected_result",
    [
        ("'Alex Smith' <test@example.com>", "test@example.com"),
        ("'Alex Smith' via [TEST] mail <test@example.com>", "'Alex Smith' via [TEST] mail <test@example.com>"),
    ],
)
def test_get_sender_from_email_message(sender_value, expected_result):
    email = AnymailInboundMessage()
    email["From"] = sender_value
    view = InboundEmailWebhookView()
    result = view.get_sender_from_email_message(email)
    assert result == expected_result
