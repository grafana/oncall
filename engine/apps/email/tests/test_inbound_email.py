import pytest, anymail, json
from apps.email.inbound import InboundEmailWebhookView
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_amazon_ses_provider_load(
    settings,
    client_with_user
):
    settings.INBOUND_EMAIL_ESP = "amazon_ses"

    test_data = {
        "foo" : "bar"
    }
    inbound_view = InboundEmailWebhookView()
    client = APIClient()
    url = reverse("integrations:inbound_email_webhook")
    with pytest.raises(anymail.exceptions.AnymailAPIError):
        response = client.post(url, data=test_data)
