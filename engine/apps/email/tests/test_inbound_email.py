import pytest, anymail
from apps.email.inbound import InboundEmailWebhookView
from django.test.client import RequestFactory

@pytest.mark.django_db
def test_amazon_ses_provider_load(
    settings
):
    result = False
    
    settings.INBOUND_EMAIL_ESP = "amazon_ses"
    rf = RequestFactory()

    inbound_view = InboundEmailWebhookView()
    try:
        inbound_view.post(rf.post('/fake-mock-location'))
        result = True
    except anymail.exceptions.AnymailAPIError:
        # We don't test anymail, but it's invocation ability
        result = True
    assert result
