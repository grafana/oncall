import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_inbound_email_webhook_head(
    settings,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
):
    settings.FEATURE_INBOUND_EMAIL_ENABLED = True
    settings.INBOUND_EMAIL_ESP = "mailgun"
    settings.INBOUND_EMAIL_DOMAIN = "test.test"
    client = APIClient()

    url = reverse("integrations:inbound_email_webhook")
    response = client.head(url)

    assert response.status_code == status.HTTP_200_OK
