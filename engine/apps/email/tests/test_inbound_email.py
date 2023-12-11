import pytest, anymail, json
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

@pytest.mark.django_db
def test_amazon_ses_provider_load(
    settings,
    make_organization_and_user_with_token,
    make_alert_receive_channel
):
    settings.INBOUND_EMAIL_ESP = "amazon_ses"
    settings.INBOUND_EMAIL_DOMAIN = "example.com"

    dummy_channel_token = "dummy-channel-token"

    mime = """From: sender@example.com
    Subject: Dummy email message
    To: %s@example.com
    Content-Type: text/plain

    Hello!
    """ % dummy_channel_token

    message = {
        "notificationType" : "Received",
        "receipt": {
            "action": {"type": "SNS"},
            "recipients": ["%s@example.com" % dummy_channel_token]
        },
        "content": "%s" % mime
    }

    dummy_sns_message_id = "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324"
    dummy_sns_payload = {
        "Type" : "Notification",
        "MessageId" : f"{dummy_sns_message_id}",
        "TopicArn" : "arn:aws:sns:us-east-1:123456789012:MyTopic",
        "Subject" : "My First Message",
        "Message" : "%s" % json.dumps(message)
    }

    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization, token=f"{dummy_channel_token}")

    client = APIClient()
    url = reverse("integrations:inbound_email_webhook")
    response = client.post(url, data=json.dumps(dummy_sns_payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"{token}",
        HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        HTTP_X_AMZ_SNS_MESSAGE_ID=f"{dummy_sns_message_id}")
    assert response.status_code == status.HTTP_200_OK
